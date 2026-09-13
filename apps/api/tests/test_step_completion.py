import asyncio
import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.job_step import JobStep
from app.models.ledger_entry import LedgerEntry
from app.repositories.assets import find_assets_by_ids
from app.repositories.job_steps import claim_next_queued_step, requeue_step
from app.repositories.jobs import find_job
from app.services.generation_runs import GENERIC_FAILURE_MESSAGE, RunSettings, run_claimed_step
from app.services.lease_reaper import FIRST_EXPIRY_ERROR
from app.services.step_claiming import claim_step
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.fakes.scripted_model_adapter import POSTER_SIZE, VIDEO_SIZE, ScriptedModelAdapter
from tests.job_api_helpers import (
    GUEST_GRANT,
    PRESET_COST,
    balance_of,
    create_queued_job,
    current_user_id,
)

LEASE_SECONDS = 300
WORKER_ID = "completion-worker"
DRAIN_WORKER = "drain-worker"
RUN_SETTINGS = RunSettings(lease_seconds=300, generation_timeout_seconds=30, download_url_ttl_seconds=3600)


async def drain_queued_steps(session_maker: async_sessionmaker[AsyncSession]) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, LEASE_SECONDS)
            await session.commit()
        if claimed is None:
            return


async def create_and_claim(guest_client, object_storage, session_maker, key: str):
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, key))
    claimed = await claim_step(session_maker, WORKER_ID, LEASE_SECONDS)
    assert claimed is not None and claimed.job_id == job_id
    return job_id, claimed


async def run_claimed(session_maker, object_storage, claimed, adapter, settings=RUN_SETTINGS) -> None:
    await run_claimed_step(
        session_maker,
        storage=object_storage,
        adapter=adapter,
        claimed=claimed,
        worker_id=WORKER_ID,
        settings=settings,
    )


async def job_snapshot(session_maker, job_id: uuid.UUID):
    async with session_maker() as session:
        job = await find_job(session, job_id)
        assert job is not None
        return job.status, job.error_message, job.output_video_asset_id, job.output_poster_asset_id


async def ledger_rows(session_maker, job_id: uuid.UUID) -> list[tuple[str, int]]:
    statement = select(LedgerEntry.kind, LedgerEntry.amount).where(LedgerEntry.job_id == job_id)
    async with session_maker() as session:
        rows = await session.execute(statement)
        return [(str(row[0]), int(row[1])) for row in rows]


async def step_snapshot(session_maker, step_id: uuid.UUID):
    statement = select(JobStep.status, JobStep.attempt, JobStep.backend, JobStep.last_error)
    async with session_maker() as session:
        row = (await session.execute(statement.where(JobStep.id == step_id))).one()
        return str(row[0]), int(row[1]), row[2], row[3]


async def asset_snapshots(session_maker, job_id: uuid.UUID) -> list[tuple[str, str, str, str, int | None]]:
    async with session_maker() as session:
        job = await find_job(session, job_id)
        assert job is not None
        ids = [asset_id for asset_id in (job.output_video_asset_id, job.output_poster_asset_id) if asset_id]
        assets = await find_assets_by_ids(session, ids)
        return [
            (asset.kind, asset.status, asset.storage_key, asset.content_type, asset.byte_size)
            for asset in assets.values()
        ]


async def test_success_uploads_outputs_settles_credits_and_succeeds(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    job_id, claimed = await create_and_claim(guest_client, object_storage, session_maker, "succ-0001")
    user_id = await current_user_id(guest_client)

    await run_claimed(session_maker, object_storage, claimed, ScriptedModelAdapter())

    video_key = f"users/{user_id}/jobs/{job_id}/video.mp4"
    poster_key = f"users/{user_id}/jobs/{job_id}/poster.jpg"
    status, error, video_asset_id, poster_asset_id = await job_snapshot(session_maker, job_id)
    assert (status, error) == ("succeeded", None)
    assert video_asset_id is not None and poster_asset_id is not None
    assert await object_storage.read_object_size(video_key) == VIDEO_SIZE
    assert await object_storage.read_object_size(poster_key) == POSTER_SIZE
    assert await step_snapshot(session_maker, claimed.id) == ("succeeded", 1, "scripted", None)
    snapshots = await asset_snapshots(session_maker, job_id)
    assert ("output_video", "ready", video_key, "video/mp4", VIDEO_SIZE) in snapshots
    assert ("output_poster", "ready", poster_key, "image/jpeg", POSTER_SIZE) in snapshots
    rows = await ledger_rows(session_maker, job_id)
    assert ("HOLD", -PRESET_COST) in rows and ("SETTLE", 0) in rows
    assert sum(1 for kind, _ in rows if kind in {"SETTLE", "RELEASE"}) == 1
    assert await balance_of(guest_client) == GUEST_GRANT - PRESET_COST


async def test_generation_error_fails_with_the_user_message_and_releases(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    job_id, claimed = await create_and_claim(guest_client, object_storage, session_maker, "err-0001")

    adapter = ScriptedModelAdapter("generation_error", user_message="Nope")
    await run_claimed(session_maker, object_storage, claimed, adapter)

    status, error, _, _ = await job_snapshot(session_maker, job_id)
    assert (status, error) == ("failed", "Nope")
    assert await step_snapshot(session_maker, claimed.id) == ("failed", 1, "scripted", "Nope")
    rows = await ledger_rows(session_maker, job_id)
    assert ("RELEASE", PRESET_COST) in rows and all(kind != "SETTLE" for kind, _ in rows)
    assert await balance_of(guest_client) == GUEST_GRANT


async def test_runtime_error_fails_with_the_generic_message_and_releases(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    job_id, claimed = await create_and_claim(guest_client, object_storage, session_maker, "err-0002")

    await run_claimed(session_maker, object_storage, claimed, ScriptedModelAdapter("runtime_error"))

    status, error, _, _ = await job_snapshot(session_maker, job_id)
    assert (status, error) == ("failed", GENERIC_FAILURE_MESSAGE)
    assert "kaboom" not in str(error)
    assert ("RELEASE", PRESET_COST) in await ledger_rows(session_maker, job_id)
    assert await balance_of(guest_client) == GUEST_GRANT


async def test_timeout_fails_with_the_generic_message_and_releases(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    job_id, claimed = await create_and_claim(guest_client, object_storage, session_maker, "err-0003")
    timeout_settings = RunSettings(
        lease_seconds=300, generation_timeout_seconds=0.2, download_url_ttl_seconds=3600
    )

    await run_claimed(session_maker, object_storage, claimed, ScriptedModelAdapter("hang"), timeout_settings)

    assert (await job_snapshot(session_maker, job_id))[:2] == ("failed", GENERIC_FAILURE_MESSAGE)
    assert ("RELEASE", PRESET_COST) in await ledger_rows(session_maker, job_id)


async def test_lost_lease_writes_nothing(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await drain_queued_steps(session_maker)
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "lost-0001"))
    user_id = await current_user_id(guest_client)
    claimed = await claim_step(session_maker, WORKER_ID, 1)
    assert claimed is not None and claimed.job_id == job_id
    lost_lease = RunSettings(lease_seconds=1, generation_timeout_seconds=30, download_url_ttl_seconds=3600)

    run = asyncio.create_task(
        run_claimed(session_maker, object_storage, claimed, ScriptedModelAdapter("hang"), lost_lease)
    )
    await asyncio.sleep(0.05)
    async with session_maker() as session:
        await requeue_step(session, claimed.id, FIRST_EXPIRY_ERROR)
        await session.commit()
    await asyncio.wait_for(run, timeout=5)

    assert await job_snapshot(session_maker, job_id) == ("running", None, None, None)
    assert await step_snapshot(session_maker, claimed.id) == ("queued", 1, None, FIRST_EXPIRY_ERROR)
    assert await ledger_rows(session_maker, job_id) == [("HOLD", -PRESET_COST)]
    assert await object_storage.read_object_size(f"users/{user_id}/jobs/{job_id}/video.mp4") is None
