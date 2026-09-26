import asyncio
import logging
import tempfile
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.ffmpeg_stitcher import StitchResult, stitch_clips
from app.adapters.model_adapter import GenerationError
from app.adapters.object_storage import ObjectStorage
from app.domain.sequence_rules import STITCH_BACKEND
from app.logging_setup import clear_job_context, set_job_context
from app.repositories.job_steps import ClaimedStep
from app.repositories.stitch_inputs import StitchInputs, load_stitch_inputs
from app.services.adapter_runs import RunSettings, renew_lease_until_lost
from app.services.generation_runs import GENERIC_FAILURE_MESSAGE
from app.services.step_completion import (
    POSTER_CONTENT_TYPE,
    VIDEO_CONTENT_TYPE,
    complete_step_failure,
    complete_step_success,
)

logger = logging.getLogger(__name__)


async def run_stitch_step(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    storage: ObjectStorage,
    claimed: ClaimedStep,
    worker_id: str,
    settings: RunSettings,
) -> None:
    inputs = await load_stitch_inputs_for_step(session_maker, claimed)
    if inputs is None:
        logger.error("step %s has no sequence inputs; skipping", claimed.id)
        return
    set_job_context(job_id=str(claimed.job_id), step_id=str(claimed.id),
                    user_id=str(inputs.user_id), backend=STITCH_BACKEND, attempt=claimed.attempt)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"hf-stitch-{claimed.id.hex[:8]}-") as directory:
        try:
            result = await stitch_with_lease(
                session_maker, storage, claimed, inputs, worker_id, Path(directory), settings
            )
            if result is None:
                clear_job_context()
                return
            video_key = f"users/{inputs.user_id}/jobs/{claimed.job_id}/video.mp4"
            poster_key = f"users/{inputs.user_id}/jobs/{claimed.job_id}/poster.jpg"
            await storage.upload_from_path(video_key, result.video_path, VIDEO_CONTENT_TYPE)
            await storage.upload_from_path(poster_key, result.poster_path, POSTER_CONTENT_TYPE)
            await complete_step_success(
                session_maker,
                step_id=claimed.id,
                job_id=claimed.job_id,
                worker_id=worker_id,
                backend=STITCH_BACKEND,
                video_key=video_key,
                poster_key=poster_key,
                video_size=result.video_path.stat().st_size,
                poster_size=result.poster_path.stat().st_size,
                duration_ms=result.duration_ms,
            )
            logger.info("sequence stitch succeeded", extra={
                "outcome": "succeeded", "generated_by": STITCH_BACKEND,
                "duration_ms": int((time.monotonic() - started) * 1000)})
            clear_job_context()
            return
        except GenerationError as error:
            user_message, last_error = error.user_message, str(error)
        except Exception as error:
            logger.exception("sequence stitch failed for step %s", claimed.id)
            user_message, last_error = GENERIC_FAILURE_MESSAGE, repr(error)
        logger.info("sequence stitch failed", extra={
            "outcome": "failed", "generated_by": STITCH_BACKEND,
            "duration_ms": int((time.monotonic() - started) * 1000)})
        await complete_step_failure(
            session_maker,
            step_id=claimed.id,
            job_id=claimed.job_id,
            worker_id=worker_id,
            backend=STITCH_BACKEND,
            last_error=last_error,
            user_message=user_message,
        )
        clear_job_context()


async def load_stitch_inputs_for_step(
    session_maker: async_sessionmaker[AsyncSession], claimed: ClaimedStep
) -> StitchInputs | None:
    async with session_maker() as session:
        return await load_stitch_inputs(session, claimed.job_id)


async def stitch_with_lease(
    session_maker: async_sessionmaker[AsyncSession],
    storage: ObjectStorage,
    claimed: ClaimedStep,
    inputs: StitchInputs,
    worker_id: str,
    work_dir: Path,
    settings: RunSettings,
) -> StitchResult | None:
    stitch_task = asyncio.create_task(
        asyncio.wait_for(
            run_stitch(storage, inputs, work_dir), settings.generation_timeout_seconds
        )
    )
    renewal_task = asyncio.create_task(
        renew_lease_until_lost(session_maker, claimed.id, worker_id, settings.lease_seconds)
    )
    try:
        done, _ = await asyncio.wait(
            {stitch_task, renewal_task}, return_when=asyncio.FIRST_COMPLETED
        )
        if renewal_task in done:
            logger.warning("lease lost for step %s; discarding the run", claimed.id)
            return None
        return stitch_task.result()
    finally:
        stitch_task.cancel()
        renewal_task.cancel()
        await asyncio.gather(stitch_task, renewal_task, return_exceptions=True)


async def run_stitch(
    storage: ObjectStorage, inputs: StitchInputs, work_dir: Path
) -> StitchResult:
    work_dir.mkdir(parents=True, exist_ok=True)
    clip_paths: list[Path] = []
    for index, clip in enumerate(inputs.clips):
        path = work_dir / f"clip-{index}.mp4"
        await storage.download_to_path(clip.storage_key, path)
        clip_paths.append(path)
    audio_path = None
    if inputs.audio_storage_key is not None:
        audio_path = work_dir / "audio"
        await storage.download_to_path(inputs.audio_storage_key, audio_path)
    trims = [(clip.trim_start_ms, clip.trim_end_ms) for clip in inputs.clips]
    return await stitch_clips(
        clip_paths, [clip.transition_in for clip in inputs.clips], audio_path, work_dir, trims
    )
