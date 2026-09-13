from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.local_motion_adapter import LocalMotionAdapter
from app.repositories.jobs import find_job
from app.services.adapter_runs import RunSettings
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.fakes.scripted_model_adapter import ScriptedModelAdapter
from tests.worker_run_helpers import (
    RecordingAdapter,
    create_and_claim,
    run_video_step,
)

EXHAUSTED = RunSettings(
    lease_seconds=300,
    generation_timeout_seconds=60,
    download_url_ttl_seconds=3600,
    paid_budget_cents=0,
)


async def test_exhausted_budget_never_invokes_the_paid_adapter(
    guest_client,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id, claimed = await create_and_claim(
        guest_client, object_storage, session_maker, "budget-0002"
    )
    primary = RecordingAdapter()
    await run_video_step(
        session_maker, object_storage, claimed, primary,
        fallback=LocalMotionAdapter(), settings=EXHAUSTED,
    )
    assert primary.calls == 0
    async with session_maker() as session:
        job = await find_job(session, job_id)
    assert job is not None and job.status == "succeeded" and job.generated_by == "local-motion"


async def test_paid_failure_falls_back_to_local_motion(
    guest_client,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id, claimed = await create_and_claim(
        guest_client, object_storage, session_maker, "fallback-1"
    )
    primary = ScriptedModelAdapter("generation_error", user_message="GPU down")
    await run_video_step(
        session_maker, object_storage, claimed, primary, fallback=LocalMotionAdapter()
    )
    async with session_maker() as session:
        job = await find_job(session, job_id)
    assert job is not None and job.status == "succeeded" and job.generated_by == "local-motion"
