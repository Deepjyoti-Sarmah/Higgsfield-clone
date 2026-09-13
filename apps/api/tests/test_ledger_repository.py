import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.credit_rules import (
    GUEST_GRANT_CREDITS,
    VIDEO_CREDIT_COST,
    hold_amount,
    release_amount,
)
from app.models.asset import Asset
from app.models.job import Job
from app.models.job_step import JobStep
from app.models.ledger_entry import LedgerEntry
from app.models.user import AppUser
from app.repositories.ledger import insert_ledger_entry, sum_user_balance

CREATED_USER_IDS: list[uuid.UUID] = []


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


async def create_user(session_maker: async_sessionmaker[AsyncSession]) -> uuid.UUID:
    async with session_maker() as session:
        user = AppUser(is_guest=True)
        session.add(user)
        await session.commit()
        CREATED_USER_IDS.append(user.id)
        return user.id


async def create_job(
    session_maker: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> uuid.UUID:
    async with session_maker() as session:
        asset = Asset(
            user_id=user_id,
            kind="input_image",
            status="ready",
            storage_key=f"tests/{uuid.uuid4().hex}.jpg",
            content_type="image/jpeg",
            byte_size=16,
        )
        session.add(asset)
        await session.flush()
        job = Job(
            user_id=user_id,
            preset_slug="dolly-in",
            input_asset_id=asset.id,
            idempotency_key=uuid.uuid4().hex,
            status="queued",
            credit_cost=VIDEO_CREDIT_COST,
        )
        session.add(job)
        await session.commit()
        return job.id


async def test_sum_user_balance_is_zero_without_entries(session_maker) -> None:
    user_id = await create_user(session_maker)

    async with session_maker() as session:
        assert await sum_user_balance(session, user_id) == 0


async def test_sum_user_balance_adds_grant_and_hold(session_maker) -> None:
    user_id = await create_user(session_maker)
    job_id = await create_job(session_maker, user_id)

    async with session_maker() as session:
        await insert_ledger_entry(session, user_id=user_id, kind="GRANT", amount=GUEST_GRANT_CREDITS)
        await insert_ledger_entry(
            session,
            user_id=user_id,
            kind="HOLD",
            amount=hold_amount(VIDEO_CREDIT_COST),
            job_id=job_id,
        )
        await session.commit()

    async with session_maker() as session:
        balance = await sum_user_balance(session, user_id)
    assert balance == GUEST_GRANT_CREDITS - VIDEO_CREDIT_COST


async def test_second_guest_grant_is_rejected(session_maker) -> None:
    user_id = await create_user(session_maker)
    async with session_maker() as session:
        await insert_ledger_entry(session, user_id=user_id, kind="GRANT", amount=GUEST_GRANT_CREDITS)
        await session.commit()

    with pytest.raises(IntegrityError):
        async with session_maker() as session:
            await insert_ledger_entry(
                session, user_id=user_id, kind="GRANT", amount=GUEST_GRANT_CREDITS
            )


async def test_second_hold_for_one_job_is_rejected(session_maker) -> None:
    user_id = await create_user(session_maker)
    job_id = await create_job(session_maker, user_id)
    async with session_maker() as session:
        await insert_ledger_entry(
            session,
            user_id=user_id,
            kind="HOLD",
            amount=hold_amount(VIDEO_CREDIT_COST),
            job_id=job_id,
        )
        await session.commit()

    with pytest.raises(IntegrityError):
        async with session_maker() as session:
            await insert_ledger_entry(
                session,
                user_id=user_id,
                kind="HOLD",
                amount=hold_amount(VIDEO_CREDIT_COST),
                job_id=job_id,
            )


async def test_settle_after_release_is_rejected(session_maker) -> None:
    user_id = await create_user(session_maker)
    job_id = await create_job(session_maker, user_id)
    async with session_maker() as session:
        await insert_ledger_entry(
            session,
            user_id=user_id,
            kind="RELEASE",
            amount=release_amount(VIDEO_CREDIT_COST),
            job_id=job_id,
        )
        await session.commit()

    with pytest.raises(IntegrityError):
        async with session_maker() as session:
            await insert_ledger_entry(
                session, user_id=user_id, kind="SETTLE", amount=0, job_id=job_id
            )


async def test_positive_hold_amount_is_rejected(session_maker) -> None:
    user_id = await create_user(session_maker)
    job_id = await create_job(session_maker, user_id)

    with pytest.raises(IntegrityError):
        async with session_maker() as session:
            await insert_ledger_entry(
                session, user_id=user_id, kind="HOLD", amount=VIDEO_CREDIT_COST, job_id=job_id
            )
