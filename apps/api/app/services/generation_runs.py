import asyncio
import logging
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.model_adapter import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    ModelAdapter,
)
from app.adapters.object_storage import ObjectStorage
from app.repositories.assets import find_user_asset
from app.repositories.job_steps import ClaimedStep, renew_step_lease
from app.repositories.jobs import find_job
from app.services.step_completion import complete_step_failure, complete_step_success

logger = logging.getLogger(__name__)

GENERIC_FAILURE_MESSAGE = "Generation failed. Your credits were refunded."
LEASE_RENEWALS_PER_LEASE = 5
VIDEO_CONTENT_TYPE = "video/mp4"
POSTER_CONTENT_TYPE = "image/jpeg"


@dataclass(frozen=True)
class RunSettings:
    lease_seconds: int
    generation_timeout_seconds: float
    download_url_ttl_seconds: int


@dataclass(frozen=True)
class StepInputs:
    user_id: uuid.UUID
    preset_slug: str
    prompt: str | None
    input_key: str


async def run_claimed_step(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    storage: ObjectStorage,
    adapter: ModelAdapter,
    claimed: ClaimedStep,
    worker_id: str,
    settings: RunSettings,
) -> None:
    inputs = await load_step_inputs(session_maker, claimed)
    if inputs is None:
        logger.error("step %s has no job or input asset; skipping", claimed.id)
        return
    with tempfile.TemporaryDirectory(prefix=f"hf-step-{claimed.id.hex[:8]}-") as directory:
        try:
            result = await run_adapter_with_lease(
                session_maker, storage, adapter, claimed, inputs, worker_id, Path(directory), settings
            )
            if result is None:
                return
            await complete_run(session_maker, storage, adapter, claimed, inputs, result, worker_id)
            return
        except GenerationError as error:
            user_message, last_error = error.user_message, str(error)
        except Exception as error:
            logger.exception("generation failed for step %s", claimed.id)
            user_message, last_error = GENERIC_FAILURE_MESSAGE, repr(error)
        await complete_step_failure(
            session_maker,
            step_id=claimed.id,
            job_id=claimed.job_id,
            worker_id=worker_id,
            backend=adapter.name,
            last_error=last_error,
            user_message=user_message,
        )


async def run_adapter_with_lease(
    session_maker: async_sessionmaker[AsyncSession],
    storage: ObjectStorage,
    adapter: ModelAdapter,
    claimed: ClaimedStep,
    inputs: StepInputs,
    worker_id: str,
    work_dir: Path,
    settings: RunSettings,
) -> GenerationResult | None:
    input_path = work_dir / "input"
    await storage.download_to_path(inputs.input_key, input_path)
    request = GenerationRequest(
        job_id=claimed.job_id,
        preset_slug=inputs.preset_slug,
        prompt=inputs.prompt,
        input_image_path=input_path,
        input_image_url=storage.create_download_url(
            inputs.input_key, settings.download_url_ttl_seconds
        ),
        work_dir=work_dir,
    )
    adapter_task = asyncio.create_task(
        asyncio.wait_for(adapter.generate_video(request), settings.generation_timeout_seconds)
    )
    renewal_task = asyncio.create_task(
        renew_lease_until_lost(session_maker, claimed.id, worker_id, settings.lease_seconds)
    )
    try:
        done, _ = await asyncio.wait({adapter_task, renewal_task}, return_when=asyncio.FIRST_COMPLETED)
        if renewal_task in done:
            logger.warning("lease lost for step %s; discarding the run", claimed.id)
            return None
        return adapter_task.result()
    finally:
        adapter_task.cancel()
        renewal_task.cancel()
        await asyncio.gather(adapter_task, renewal_task, return_exceptions=True)


async def renew_lease_until_lost(
    session_maker: async_sessionmaker[AsyncSession],
    step_id: uuid.UUID,
    worker_id: str,
    lease_seconds: int,
) -> bool:
    interval_seconds = lease_seconds / LEASE_RENEWALS_PER_LEASE
    while True:
        await asyncio.sleep(interval_seconds)
        async with session_maker() as session:
            renewed = await renew_step_lease(session, step_id, worker_id, lease_seconds)
            if renewed:
                await session.commit()
        if not renewed:
            return True


async def complete_run(
    session_maker: async_sessionmaker[AsyncSession],
    storage: ObjectStorage,
    adapter: ModelAdapter,
    claimed: ClaimedStep,
    inputs: StepInputs,
    result: GenerationResult,
    worker_id: str,
) -> None:
    video_key = f"users/{inputs.user_id}/jobs/{claimed.job_id}/video.mp4"
    poster_key = f"users/{inputs.user_id}/jobs/{claimed.job_id}/poster.jpg"
    await storage.upload_from_path(video_key, result.video_path, VIDEO_CONTENT_TYPE)
    await storage.upload_from_path(poster_key, result.poster_path, POSTER_CONTENT_TYPE)
    await complete_step_success(
        session_maker,
        step_id=claimed.id,
        job_id=claimed.job_id,
        worker_id=worker_id,
        backend=adapter.name,
        video_key=video_key,
        poster_key=poster_key,
        video_size=result.video_path.stat().st_size,
        poster_size=result.poster_path.stat().st_size,
    )


async def load_step_inputs(
    session_maker: async_sessionmaker[AsyncSession], claimed: ClaimedStep
) -> StepInputs | None:
    async with session_maker() as session:
        job = await find_job(session, claimed.job_id)
        if job is None:
            return None
        asset = await find_user_asset(session, job.user_id, job.input_asset_id)
        if asset is None:
            return None
        return StepInputs(
            user_id=job.user_id,
            preset_slug=job.preset_slug,
            prompt=job.prompt,
            input_key=asset.storage_key,
        )
