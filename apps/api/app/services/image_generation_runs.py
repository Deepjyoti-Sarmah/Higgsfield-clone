import asyncio
import logging
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.image_model_adapter import ImageGenerationRequest, ImageModelAdapter
from app.adapters.model_adapter import GenerationError
from app.adapters.object_storage import ObjectStorage
from app.logging_setup import clear_job_context, set_job_context, truncate_prompt
from app.repositories.job_steps import ClaimedStep
from app.repositories.jobs import find_job
from app.services.adapter_runs import RunSettings, renew_lease_until_lost
from app.services.generation_runs import GENERIC_FAILURE_MESSAGE
from app.services.image_step_completion import complete_image_step_success
from app.services.step_completion import complete_step_failure

logger = logging.getLogger(__name__)

IMAGE_CONTENT_TYPE = "image/png"


@dataclass(frozen=True)
class ImageStepInput:
    user_id: uuid.UUID
    prompt: str
    aspect_ratio: str
    quality: str
    count: int


async def run_image_step(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    storage: ObjectStorage,
    adapter: ImageModelAdapter,
    claimed: ClaimedStep,
    worker_id: str,
    settings: RunSettings,
) -> None:
    inputs = await load_image_step_input(session_maker, claimed)
    if inputs is None:
        logger.error("step %s has no image job or params; skipping", claimed.id)
        return
    set_job_context(job_id=str(claimed.job_id), step_id=str(claimed.id),
                    user_id=str(inputs.user_id), backend=adapter.name, attempt=claimed.attempt)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"hf-image-{claimed.id.hex[:8]}-") as directory:
        try:
            paths = await generate_with_lease(
                session_maker, adapter, claimed, inputs, worker_id, Path(directory), settings
            )
            if paths is None:
                clear_job_context()
                return
            images = await upload_images(storage, inputs, claimed.job_id, paths)
            await complete_image_step_success(
                session_maker,
                step_id=claimed.id,
                job_id=claimed.job_id,
                worker_id=worker_id,
                backend=adapter.name,
                images=images,
            )
            logger.info("image generation succeeded", extra={
                "outcome": "succeeded", "generated_by": adapter.name,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "prompt": truncate_prompt(inputs.prompt)})
            clear_job_context()
            return
        except GenerationError as error:
            user_message, last_error = error.user_message, str(error)
        except Exception as error:
            logger.exception("image generation failed for step %s", claimed.id)
            user_message, last_error = GENERIC_FAILURE_MESSAGE, repr(error)
        logger.info("image generation failed", extra={
            "outcome": "failed", "generated_by": adapter.name,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "prompt": truncate_prompt(inputs.prompt)})
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


async def load_image_step_input(
    session_maker: async_sessionmaker[AsyncSession], claimed: ClaimedStep
) -> ImageStepInput | None:
    async with session_maker() as session:
        job = await find_job(session, claimed.job_id)
        if job is None or job.kind != "image" or job.prompt is None:
            return None
        if job.aspect_ratio is None or job.quality is None or job.image_count is None:
            return None
        return ImageStepInput(
            user_id=job.user_id,
            prompt=job.prompt,
            aspect_ratio=job.aspect_ratio,
            quality=job.quality,
            count=job.image_count,
        )


async def generate_with_lease(
    session_maker: async_sessionmaker[AsyncSession],
    adapter: ImageModelAdapter,
    claimed: ClaimedStep,
    inputs: ImageStepInput,
    worker_id: str,
    work_dir: Path,
    settings: RunSettings,
) -> list[Path] | None:
    request = ImageGenerationRequest(
        job_id=claimed.job_id,
        prompt=inputs.prompt,
        aspect_ratio=inputs.aspect_ratio,
        quality=inputs.quality,
        count=inputs.count,
        work_dir=work_dir,
    )
    adapter_task = asyncio.create_task(
        asyncio.wait_for(adapter.generate_image(request), settings.generation_timeout_seconds)
    )
    renewal_task = asyncio.create_task(
        renew_lease_until_lost(session_maker, claimed.id, worker_id, settings.lease_seconds)
    )
    try:
        done, _ = await asyncio.wait(
            {adapter_task, renewal_task}, return_when=asyncio.FIRST_COMPLETED
        )
        if renewal_task in done:
            logger.warning("lease lost for step %s; discarding the run", claimed.id)
            return None
        return adapter_task.result().image_paths
    finally:
        adapter_task.cancel()
        renewal_task.cancel()
        await asyncio.gather(adapter_task, renewal_task, return_exceptions=True)


async def upload_images(
    storage: ObjectStorage, inputs: ImageStepInput, job_id: uuid.UUID, paths: list[Path]
) -> list[tuple[int, str, int]]:
    images: list[tuple[int, str, int]] = []
    for position, path in enumerate(paths, start=1):
        key = f"users/{inputs.user_id}/jobs/{job_id}/image-{position}.png"
        await storage.upload_from_path(key, path, IMAGE_CONTENT_TYPE)
        images.append((position, key, path.stat().st_size))
    return images
