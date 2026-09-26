import asyncio
import logging
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.face_swap_adapter import FaceSwapAdapterProtocol
from app.adapters.model_adapter import GenerationError
from app.adapters.object_storage import ObjectStorage
from app.logging_setup import clear_job_context, set_job_context
from app.repositories.assets import find_assets_by_ids
from app.repositories.job_steps import ClaimedStep
from app.repositories.jobs import find_job
from app.services.adapter_runs import RunSettings, renew_lease_until_lost
from app.services.generation_runs import GENERIC_FAILURE_MESSAGE
from app.services.image_step_completion import complete_image_step_success
from app.services.step_completion import complete_step_failure

logger = logging.getLogger(__name__)

IMAGE_CONTENT_TYPE = "image/png"
IMAGE_POSITION = 0


@dataclass(frozen=True)
class FaceSwapStepInput:
    user_id: uuid.UUID
    source_key: str
    target_key: str


async def run_faceswap_step(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    storage: ObjectStorage,
    adapter: FaceSwapAdapterProtocol,
    claimed: ClaimedStep,
    worker_id: str,
    settings: RunSettings,
) -> None:
    inputs = await load_faceswap_step_input(session_maker, claimed)
    if inputs is None:
        logger.error("step %s has no faceswap job or assets; skipping", claimed.id)
        return
    set_job_context(job_id=str(claimed.job_id), step_id=str(claimed.id),
                    user_id=str(inputs.user_id), backend=adapter.name, attempt=claimed.attempt)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"hf-faceswap-{claimed.id.hex[:8]}-") as directory:
        try:
            image_bytes = await swap_with_lease(
                session_maker, storage, adapter, claimed, inputs, worker_id, settings
            )
            if image_bytes is None:
                clear_job_context()
                return
            key = await _upload_result(storage, inputs, claimed.job_id, Path(directory), image_bytes)
            await complete_image_step_success(
                session_maker,
                step_id=claimed.id,
                job_id=claimed.job_id,
                worker_id=worker_id,
                backend=adapter.name,
                images=[(IMAGE_POSITION, key, len(image_bytes))],
            )
            _log_outcome("succeeded", adapter.name, started)
            clear_job_context()
            return
        except GenerationError as error:
            user_message, last_error = error.user_message, str(error)
        except Exception as error:
            logger.exception("face swap failed for step %s", claimed.id)
            user_message, last_error = GENERIC_FAILURE_MESSAGE, repr(error)
        _log_outcome("failed", adapter.name, started)
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


def _log_outcome(outcome: str, backend: str, started: float) -> None:
    logger.info("face swap %s", outcome, extra={
        "outcome": outcome, "generated_by": backend,
        "duration_ms": int((time.monotonic() - started) * 1000)})


async def _upload_result(
    storage: ObjectStorage,
    inputs: FaceSwapStepInput,
    job_id: uuid.UUID,
    work_dir: Path,
    image_bytes: bytes,
) -> str:
    path = work_dir / "swap.png"
    path.write_bytes(image_bytes)
    key = f"users/{inputs.user_id}/jobs/{job_id}/image-1.png"
    await storage.upload_from_path(key, path, IMAGE_CONTENT_TYPE)
    return key


async def load_faceswap_step_input(
    session_maker: async_sessionmaker[AsyncSession], claimed: ClaimedStep
) -> FaceSwapStepInput | None:
    async with session_maker() as session:
        job = await find_job(session, claimed.job_id)
        if job is None or job.kind != "faceswap":
            return None
        if job.face_source_asset_id is None or job.face_target_asset_id is None:
            return None
        assets = await find_assets_by_ids(
            session, [job.face_source_asset_id, job.face_target_asset_id]
        )
        source = assets.get(job.face_source_asset_id)
        target = assets.get(job.face_target_asset_id)
        if source is None or target is None:
            return None
        return FaceSwapStepInput(
            user_id=job.user_id, source_key=source.storage_key, target_key=target.storage_key
        )


async def swap_with_lease(
    session_maker: async_sessionmaker[AsyncSession],
    storage: ObjectStorage,
    adapter: FaceSwapAdapterProtocol,
    claimed: ClaimedStep,
    inputs: FaceSwapStepInput,
    worker_id: str,
    settings: RunSettings,
) -> bytes | None:
    source_url = storage.create_download_url(inputs.source_key, settings.download_url_ttl_seconds)
    target_url = storage.create_download_url(inputs.target_key, settings.download_url_ttl_seconds)
    adapter_task = asyncio.create_task(
        asyncio.wait_for(adapter.swap(source_url, target_url), settings.generation_timeout_seconds)
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
        return adapter_task.result()
    finally:
        adapter_task.cancel()
        renewal_task.cancel()
        await asyncio.gather(adapter_task, renewal_task, return_exceptions=True)
