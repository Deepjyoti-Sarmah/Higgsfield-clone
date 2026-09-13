import asyncio
import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.job_states import statuses_allowed_before
from app.models.job_step import JobStep
from app.repositories.job_steps import claim_next_queued_step
from app.repositories.jobs import read_job_status, transition_job_status
from app.services.step_claiming import claim_step
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import create_queued_job
from tests.job_event_helpers import open_broker, wait_for_wake_up

LEASE_SECONDS = 300
DRAIN_WORKER = "drain-worker"


async def drain_queued_steps(session_maker: async_sessionmaker[AsyncSession]) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, LEASE_SECONDS)
            await session.commit()
        if claimed is None:
            return


async def job_status(session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID) -> str | None:
    async with session_maker() as session:
        return await read_job_status(session, job_id)


async def step_lease_state(
    session_maker: async_sessionmaker[AsyncSession], step_id: uuid.UUID
) -> tuple[str, str | None]:
    async with session_maker() as session:
        row = (
            await session.execute(
                select(JobStep.status, JobStep.lease_owner).where(JobStep.id == step_id)
            )
        ).one()
        return str(row[0]), row[1]


async def test_parallel_claim_step_awards_the_step_to_one_worker(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "claim-key-0001"))

    async with open_broker(session_maker) as broker:
        wake_up = broker.subscribe(job_id)
        first, second = await asyncio.gather(
            claim_step(session_maker, "worker-a", LEASE_SECONDS),
            claim_step(session_maker, "worker-b", LEASE_SECONDS),
        )
        notified = await wait_for_wake_up(wake_up)

    winners = [claimed for claimed in (first, second) if claimed is not None]
    assert len(winners) == 1
    assert winners[0].job_id == job_id
    assert winners[0].attempt == 1
    assert notified is True
    assert await job_status(session_maker, job_id) == "running"
    step_status, lease_owner = await step_lease_state(session_maker, winners[0].id)
    assert step_status == "running"
    assert lease_owner in {"worker-a", "worker-b"}


async def test_claim_step_returns_none_when_the_queue_is_empty(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)

    assert await claim_step(session_maker, "worker-a", LEASE_SECONDS) is None


async def test_claim_step_abandons_a_step_whose_job_is_already_terminal(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    dead_job = uuid.UUID(await create_queued_job(guest_client, object_storage, "claim-key-0002"))
    async with session_maker() as session:
        failed = await transition_job_status(
            session,
            dead_job,
            "failed",
            allowed_from=statuses_allowed_before("failed"),
            error_message="settled elsewhere",
        )
        assert failed
        await session.commit()
    async with session_maker() as session:
        dead_step_id = await session.scalar(select(JobStep.id).where(JobStep.job_id == dead_job))
    assert dead_step_id is not None

    assert await claim_step(session_maker, "worker-a", LEASE_SECONDS) is None
    assert await step_lease_state(session_maker, dead_step_id) == ("failed", None)

    live_job = uuid.UUID(await create_queued_job(guest_client, object_storage, "claim-key-0003"))
    claimed = await claim_step(session_maker, "worker-a", LEASE_SECONDS)
    assert claimed is not None and claimed.job_id == live_job
