import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import NamedTuple

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.credit_rules import VIDEO_CREDIT_COST
from app.models.asset import Asset
from app.models.job import Job
from app.models.job_step import JobStep
from app.models.ledger_entry import LedgerEntry
from app.models.user import AppUser
from app.repositories.assets import insert_asset
from app.repositories.job_steps import (
    ClaimedStep,
    claim_next_queued_step,
    finish_step,
    insert_job_step,
    lock_expired_steps,
    renew_step_lease,
)
from app.repositories.jobs import insert_job

LEASE_SECONDS = 300
DRAIN_WORKER = "drain-worker"
CREATED_USER_IDS: list[uuid.UUID] = []


class CreatedStep(NamedTuple):
    job_id: uuid.UUID
    step_id: uuid.UUID
    user_id: uuid.UUID


async def delete_created_rows(session: AsyncSession, user_ids: list[uuid.UUID]) -> None:
    job_ids = select(Job.id).where(Job.user_id.in_(user_ids))
    await session.execute(delete(JobStep).where(JobStep.job_id.in_(job_ids)))
    await session.execute(delete(LedgerEntry).where(LedgerEntry.user_id.in_(user_ids)))
    await session.execute(delete(Job).where(Job.user_id.in_(user_ids)))
    await session.execute(delete(Asset).where(Asset.user_id.in_(user_ids)))
    await session.execute(delete(AppUser).where(AppUser.id.in_(user_ids)))
    await session.commit()


@pytest.fixture(autouse=True)
async def remove_created_rows(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[None]:
    CREATED_USER_IDS.clear()
    yield
    if CREATED_USER_IDS:
        async with session_maker() as session:
            await delete_created_rows(session, list(CREATED_USER_IDS))


async def create_queued_step(session_maker: async_sessionmaker[AsyncSession]) -> CreatedStep:
    async with session_maker() as session:
        user = AppUser(is_guest=True)
        session.add(user)
        await session.flush()
        asset = await insert_asset(
            session,
            asset_id=uuid.uuid4(),
            user_id=user.id,
            kind="input_image",
            status="ready",
            storage_key=f"tests/{uuid.uuid4().hex}.jpg",
            content_type="image/jpeg",
            byte_size=16,
        )
        job = await insert_job(
            session,
            user_id=user.id,
            preset_slug="dolly-in",
            input_asset_id=asset.id,
            prompt=None,
            idempotency_key=uuid.uuid4().hex,
            credit_cost=VIDEO_CREDIT_COST,
        )
        step = await insert_job_step(session, job.id, "generate_video")
        await session.commit()
        CREATED_USER_IDS.append(user.id)
        return CreatedStep(job_id=job.id, step_id=step.id, user_id=user.id)


async def set_step_lease(
    session_maker: async_sessionmaker[AsyncSession],
    step_id: uuid.UUID,
    *,
    owner: str,
    expires_in_seconds: float,
) -> None:
    async with session_maker() as session:
        await session.execute(
            text(
                "UPDATE job_step SET status = 'running', lease_owner = :owner,"
                " lease_expires_at = now() + make_interval(secs => :secs), attempt = attempt + 1"
                " WHERE id = :step_id"
            ),
            {"owner": owner, "secs": expires_in_seconds, "step_id": step_id},
        )
        await session.commit()


async def drain_queued_steps(session_maker: async_sessionmaker[AsyncSession]) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, LEASE_SECONDS)
            await session.commit()
        if claimed is None:
            return


async def claim_in_own_transaction(
    session_maker: async_sessionmaker[AsyncSession], worker_id: str
) -> ClaimedStep | None:
    async with session_maker() as session:
        claimed = await claim_next_queued_step(session, worker_id, LEASE_SECONDS)
        await session.commit()
        return claimed


async def test_double_claim_awards_exactly_one_worker(session_maker) -> None:
    await drain_queued_steps(session_maker)
    created = await create_queued_step(session_maker)

    first, second = await asyncio.gather(
        claim_in_own_transaction(session_maker, "worker-a"),
        claim_in_own_transaction(session_maker, "worker-b"),
    )

    winners = [claimed for claimed in (first, second) if claimed is not None]
    assert len(winners) == 1
    assert winners[0].id == created.step_id
    assert winners[0].job_id == created.job_id
    assert winners[0].attempt == 1


async def test_renew_step_lease_only_succeeds_for_the_owner(session_maker) -> None:
    created = await create_queued_step(session_maker)
    await set_step_lease(session_maker, created.step_id, owner="owner", expires_in_seconds=60)

    async with session_maker() as session:
        assert await renew_step_lease(session, created.step_id, "intruder", LEASE_SECONDS) is False
    async with session_maker() as session:
        renewed = await renew_step_lease(session, created.step_id, "owner", LEASE_SECONDS)
        await session.commit()
    assert renewed is True


async def test_finish_step_only_succeeds_for_the_owner(session_maker) -> None:
    created = await create_queued_step(session_maker)
    await set_step_lease(session_maker, created.step_id, owner="owner", expires_in_seconds=60)

    async with session_maker() as session:
        lost = await finish_step(session, created.step_id, "intruder", "succeeded", backend="mock")
    async with session_maker() as session:
        finished = await finish_step(session, created.step_id, "owner", "succeeded", backend="mock")
        await session.commit()

    assert lost is False
    assert finished is True


async def test_lock_expired_steps_skips_locked_and_unexpired_steps(session_maker) -> None:
    expired = await create_queued_step(session_maker)
    locked = await create_queued_step(session_maker)
    fresh = await create_queued_step(session_maker)
    await set_step_lease(session_maker, expired.step_id, owner="crashed", expires_in_seconds=-60)
    await set_step_lease(session_maker, locked.step_id, owner="alive", expires_in_seconds=-120)
    await set_step_lease(session_maker, fresh.step_id, owner="alive", expires_in_seconds=60)

    holder = session_maker()
    try:
        await holder.execute(
            text("SELECT id FROM job_step WHERE id = :step_id FOR UPDATE"),
            {"step_id": locked.step_id},
        )
        async with session_maker() as session:
            found = await lock_expired_steps(session, limit=100)
            await session.commit()
    finally:
        await holder.rollback()
        await holder.close()

    locked_out = {step.id for step in found}
    assert expired.step_id in locked_out
    assert locked.step_id not in locked_out
    assert fresh.step_id not in locked_out
    reaped = next(step for step in found if step.id == expired.step_id)
    assert reaped.job_id == expired.job_id
    assert reaped.user_id == expired.user_id
    assert reaped.credit_cost == VIDEO_CREDIT_COST
