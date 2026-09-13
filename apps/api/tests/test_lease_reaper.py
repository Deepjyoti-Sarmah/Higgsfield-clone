import uuid

from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.job import Job
from app.models.job_step import JobStep
from app.models.ledger_entry import LedgerEntry
from app.repositories.job_steps import claim_next_queued_step
from app.services.lease_reaper import (
    FIRST_EXPIRY_ERROR,
    SECOND_EXPIRY_ERROR,
    TIMEOUT_USER_MESSAGE,
    reap_expired_steps,
)
from app.services.step_claiming import claim_step
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import GUEST_GRANT, PRESET_COST, balance_of, create_queued_job

LEASE_SECONDS = 300
WORKER_ID = "reaper-test-worker"
DRAIN_WORKER = "drain-worker"


async def drain_queued_steps(session_maker: async_sessionmaker[AsyncSession]) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, LEASE_SECONDS)
            await session.commit()
        if claimed is None:
            return


async def expire_lease(session_maker: async_sessionmaker[AsyncSession], step_id: uuid.UUID) -> None:
    async with session_maker() as session:
        await session.execute(
            text(
                "UPDATE job_step SET lease_expires_at = now() - interval '1 minute'"
                " WHERE id = :step_id"
            ),
            {"step_id": step_id},
        )
        await session.commit()


async def job_status(session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID) -> str | None:
    async with session_maker() as session:
        return await session.scalar(select(Job.status).where(Job.id == job_id))


async def job_error_message(
    session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID
) -> str | None:
    async with session_maker() as session:
        return await session.scalar(select(Job.error_message).where(Job.id == job_id))


async def step_snapshot(
    session_maker: async_sessionmaker[AsyncSession], step_id: uuid.UUID
) -> tuple[str, int, str | None, str | None]:
    async with session_maker() as session:
        row = (
            await session.execute(
                select(JobStep.status, JobStep.attempt, JobStep.lease_owner, JobStep.last_error).where(
                    JobStep.id == step_id
                )
            )
        ).one()
        return str(row[0]), int(row[1]), row[2], row[3]


async def ledger_rows(
    session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID
) -> list[tuple[str, int]]:
    async with session_maker() as session:
        rows = await session.execute(
            select(LedgerEntry.kind, LedgerEntry.amount).where(LedgerEntry.job_id == job_id)
        )
        return [(str(row[0]), int(row[1])) for row in rows]


async def test_first_expiry_requeues_then_second_fails_and_refunds(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "reaper-key-0001"))

    first = await claim_step(session_maker, WORKER_ID, LEASE_SECONDS)
    assert first is not None and first.job_id == job_id
    await expire_lease(session_maker, first.id)

    assert await reap_expired_steps(session_maker) >= 1

    assert await step_snapshot(session_maker, first.id) == ("queued", 1, None, FIRST_EXPIRY_ERROR)
    assert await job_status(session_maker, job_id) == "queued"
    assert await balance_of(guest_client) == GUEST_GRANT - PRESET_COST
    assert ("RELEASE", PRESET_COST) not in await ledger_rows(session_maker, job_id)

    second = await claim_step(session_maker, WORKER_ID, LEASE_SECONDS)
    assert second is not None and second.job_id == job_id
    assert second.attempt == 2
    await expire_lease(session_maker, second.id)

    assert await reap_expired_steps(session_maker) >= 1

    assert await step_snapshot(session_maker, second.id) == (
        "failed",
        2,
        WORKER_ID,
        SECOND_EXPIRY_ERROR,
    )
    assert await job_status(session_maker, job_id) == "failed"
    assert await job_error_message(session_maker, job_id) == TIMEOUT_USER_MESSAGE
    assert ("RELEASE", PRESET_COST) in await ledger_rows(session_maker, job_id)
    assert await balance_of(guest_client) == GUEST_GRANT


async def test_reaper_leaves_a_step_with_a_live_lease_alone(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "reaper-key-0002"))
    claimed = await claim_step(session_maker, WORKER_ID, LEASE_SECONDS)
    assert claimed is not None and claimed.job_id == job_id

    await reap_expired_steps(session_maker)

    assert await step_snapshot(session_maker, claimed.id) == (
        "running",
        1,
        WORKER_ID,
        None,
    )
    assert await job_status(session_maker, job_id) == "running"
    assert ("RELEASE", PRESET_COST) not in await ledger_rows(session_maker, job_id)
