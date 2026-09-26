import asyncio
import json
import logging
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.ffmpeg_process import run_ffmpeg
from app.adapters.model_adapter import GenerationError
from app.adapters.object_storage import ObjectStorage
from app.adapters.video_face_swap_adapter import VideoFaceSwapAdapterProtocol
from app.logging_setup import clear_job_context, set_job_context
from app.repositories.assets import find_assets_by_ids
from app.repositories.job_steps import ClaimedStep
from app.repositories.jobs import find_job
from app.services.adapter_runs import RunSettings, renew_lease_until_lost
from app.services.generation_runs import GENERIC_FAILURE_MESSAGE
from app.services.step_completion import (
    POSTER_CONTENT_TYPE,
    VIDEO_CONTENT_TYPE,
    complete_step_failure,
    complete_step_success,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VideoFaceSwapStepInput:
    user_id: uuid.UUID
    source_key: str
    target_key: str


@dataclass(frozen=True)
class VerifiedVideo:
    duration_ms: int
    width: int
    height: int


async def run_video_faceswap_step(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    storage: ObjectStorage,
    adapter: VideoFaceSwapAdapterProtocol,
    claimed: ClaimedStep,
    worker_id: str,
    settings: RunSettings,
) -> None:
    inputs = await load_video_faceswap_step_input(session_maker, claimed)
    if inputs is None:
        logger.error("step %s has no video faceswap job or assets; skipping", claimed.id)
        return
    set_job_context(job_id=str(claimed.job_id), step_id=str(claimed.id),
                    user_id=str(inputs.user_id), backend=adapter.name, attempt=claimed.attempt)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"hf-video-swap-{claimed.id.hex[:8]}-") as directory:
        try:
            video_bytes = await swap_video_with_lease(
                session_maker, storage, adapter, claimed, inputs, worker_id, settings)
            if video_bytes is None:
                clear_job_context()
                return
            work_dir = Path(directory)
            video_path = work_dir / "swap.mp4"
            video_path.write_bytes(video_bytes)
            verified = await verify_video_output(video_path)
            poster_path = work_dir / "poster.jpg"
            await run_ffmpeg(["-ss", f"{min(verified.duration_ms / 2000, 1.0):.2f}",
                              "-i", str(video_path), "-frames:v", "1", "-q:v", "3",
                              str(poster_path)])
            base = f"users/{inputs.user_id}/jobs/{claimed.job_id}"
            await storage.upload_from_path(f"{base}/video.mp4", video_path, VIDEO_CONTENT_TYPE)
            await storage.upload_from_path(f"{base}/poster.jpg", poster_path, POSTER_CONTENT_TYPE)
            await complete_step_success(
                session_maker, step_id=claimed.id, job_id=claimed.job_id, worker_id=worker_id,
                backend=adapter.name, video_key=f"{base}/video.mp4", poster_key=f"{base}/poster.jpg",
                video_size=len(video_bytes), poster_size=poster_path.stat().st_size,
                duration_ms=verified.duration_ms)
            logger.info("video face swap succeeded", extra={
                "outcome": "succeeded", "generated_by": adapter.name,
                "duration_ms": int((time.monotonic() - started) * 1000)})
            clear_job_context()
            return
        except GenerationError as error:
            user_message, last_error = error.user_message, str(error)
        except Exception as error:
            logger.exception("video face swap failed for step %s", claimed.id)
            user_message, last_error = GENERIC_FAILURE_MESSAGE, repr(error)
        logger.info("video face swap failed", extra={
            "outcome": "failed", "generated_by": adapter.name,
            "duration_ms": int((time.monotonic() - started) * 1000)})
        await complete_step_failure(
            session_maker, step_id=claimed.id, job_id=claimed.job_id, worker_id=worker_id,
            backend=adapter.name, last_error=last_error, user_message=user_message)
        clear_job_context()


async def verify_video_output(path: Path) -> VerifiedVideo:
    process = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
        "-of", "json", str(path), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, _ = await process.communicate()
    verified = _parse_probe(stdout)
    if verified is None:
        raise GenerationError(GENERIC_FAILURE_MESSAGE)
    return verified


def _parse_probe(raw: bytes) -> VerifiedVideo | None:
    try:
        payload: Any = json.loads(raw.decode() or "{}")
    except ValueError:
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("streams"), list):
        return None
    video = next((item for item in payload["streams"] if isinstance(item, dict)
                  and item.get("codec_type") == "video"), None)
    if video is None:
        return None
    width, height = video.get("width"), video.get("height")
    section = payload.get("format")
    duration = section.get("duration") if isinstance(section, dict) else None
    if isinstance(duration, bool) or not isinstance(duration, (str, int, float)):
        return None
    try:
        duration_ms = int(float(duration) * 1000)
    except (TypeError, ValueError):
        return None
    if duration_ms <= 0 or not isinstance(width, int) or width <= 0:
        return None
    if not isinstance(height, int) or height <= 0:
        return None
    return VerifiedVideo(duration_ms=duration_ms, width=width, height=height)


async def load_video_faceswap_step_input(
    session_maker: async_sessionmaker[AsyncSession], claimed: ClaimedStep
) -> VideoFaceSwapStepInput | None:
    async with session_maker() as session:
        job = await find_job(session, claimed.job_id)
        if job is None or job.kind != "video_faceswap":
            return None
        if job.face_source_asset_id is None or job.face_target_asset_id is None:
            return None
        assets = await find_assets_by_ids(session, [job.face_source_asset_id, job.face_target_asset_id])
        source = assets.get(job.face_source_asset_id)
        target = assets.get(job.face_target_asset_id)
        if source is None or target is None:
            return None
        return VideoFaceSwapStepInput(
            user_id=job.user_id, source_key=source.storage_key, target_key=target.storage_key)


async def swap_video_with_lease(
    session_maker: async_sessionmaker[AsyncSession],
    storage: ObjectStorage,
    adapter: VideoFaceSwapAdapterProtocol,
    claimed: ClaimedStep,
    inputs: VideoFaceSwapStepInput,
    worker_id: str,
    settings: RunSettings,
) -> bytes | None:
    source_url = storage.create_download_url(inputs.source_key, settings.download_url_ttl_seconds)
    target_url = storage.create_download_url(inputs.target_key, settings.download_url_ttl_seconds)
    adapter_task = asyncio.create_task(asyncio.wait_for(
        adapter.swap_video(source_url, target_url), settings.generation_timeout_seconds))
    renewal_task = asyncio.create_task(
        renew_lease_until_lost(session_maker, claimed.id, worker_id, settings.lease_seconds))
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
