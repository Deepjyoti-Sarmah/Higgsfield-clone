import logging
import tempfile
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.model_adapter import GenerationError, GenerationResult, ModelAdapter
from app.adapters.object_storage import ObjectStorage
from app.logging_setup import clear_job_context, set_job_context, truncate_prompt
from app.repositories.job_steps import ClaimedStep
from app.services.adapter_runs import RunSettings, run_adapter_with_fallback
from app.services.step_completion import complete_step_failure, complete_step_success
from app.services.step_inputs import StepInputs, load_step_inputs

__all__ = ["GENERIC_FAILURE_MESSAGE", "RunSettings", "StepInputs", "complete_run", "run_claimed_step"]

logger = logging.getLogger(__name__)

GENERIC_FAILURE_MESSAGE = "Generation failed. Your credits were refunded."
VIDEO_CONTENT_TYPE = "video/mp4"
POSTER_CONTENT_TYPE = "image/jpeg"


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


async def run_claimed_step(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    storage: ObjectStorage,
    adapter: ModelAdapter,
    claimed: ClaimedStep,
    worker_id: str,
    settings: RunSettings,
    fallback_adapter: ModelAdapter | None = None,
) -> None:
    inputs = await load_step_inputs(session_maker, claimed)
    if inputs is None:
        logger.error("step %s has no job or input asset; skipping", claimed.id)
        return
    set_job_context(job_id=str(claimed.job_id), step_id=str(claimed.id),
                    user_id=str(inputs.user_id), backend=adapter.name, attempt=claimed.attempt)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"hf-step-{claimed.id.hex[:8]}-") as directory:
        try:
            outcome = await run_adapter_with_fallback(
                session_maker,
                storage=storage,
                primary=adapter,
                fallback=fallback_adapter,
                claimed=claimed,
                inputs=inputs,
                worker_id=worker_id,
                work_dir=Path(directory),
                settings=settings,
            )
            if outcome is None:
                clear_job_context()
                return
            result, backend = outcome
            await complete_run(session_maker, storage, claimed, inputs, result, worker_id, backend)
            logger.info("video generation succeeded", extra={
                "outcome": "succeeded", "generated_by": backend,
                "duration_ms": _elapsed_ms(started), "prompt": truncate_prompt(inputs.prompt)})
            clear_job_context()
            return
        except GenerationError as error:
            user_message, last_error = error.user_message, str(error)
        except Exception as error:
            logger.exception("generation failed for step %s", claimed.id)
            user_message, last_error = GENERIC_FAILURE_MESSAGE, repr(error)
        logger.info("video generation failed", extra={
            "outcome": "failed", "generated_by": adapter.name,
            "duration_ms": _elapsed_ms(started), "prompt": truncate_prompt(inputs.prompt)})
        await complete_step_failure(
            session_maker,
            step_id=claimed.id,
            job_id=claimed.job_id,
            worker_id=worker_id,
            backend=adapter.name,
            last_error=last_error,
            user_message=user_message,
        )
        clear_job_context()


async def complete_run(
    session_maker: async_sessionmaker[AsyncSession],
    storage: ObjectStorage,
    claimed: ClaimedStep,
    inputs: StepInputs,
    result: GenerationResult,
    worker_id: str,
    backend: str,
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
        backend=backend,
        video_key=video_key,
        poster_key=poster_key,
        video_size=result.video_path.stat().st_size,
        poster_size=result.poster_path.stat().st_size,
    )
