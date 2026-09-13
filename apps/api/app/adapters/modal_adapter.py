import asyncio
import base64
import binascii
import logging
from pathlib import Path
from typing import Any, cast

import httpx

from app.adapters.model_adapter import (
    BackendNotConfiguredError,
    GenerationError,
    GenerationRequest,
    GenerationResult,
)
from app.settings import Settings

logger = logging.getLogger(__name__)

VIDEO_FILENAME = "video.mp4"
POSTER_FILENAME = "poster.jpg"
MODAL_FAILURE_MESSAGE = "The AI backend failed. Your credits were refunded."
MODAL_TIMEOUT_MESSAGE = "The AI backend timed out. Your credits were refunded."


class ModalAdapter:
    name = "modal"

    def __init__(self, settings: Settings) -> None:
        self._endpoint_url = settings.modal_endpoint_url
        self._webhook_secret = settings.modal_webhook_secret
        self._timeout_seconds = settings.generation_timeout_seconds

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        if not self._endpoint_url:
            raise BackendNotConfiguredError("modal backend not configured: set MODAL_ENDPOINT_URL")
        payload = await self._post_clip(request.input_image_url, request.prompt or "")
        video_bytes, width, height, duration_ms = _parse_clip_payload(payload)
        request.work_dir.mkdir(parents=True, exist_ok=True)
        video_path = request.work_dir / VIDEO_FILENAME
        video_path.write_bytes(video_bytes)
        poster_path = request.work_dir / POSTER_FILENAME
        await _extract_poster(video_path, poster_path)
        return GenerationResult(video_path, poster_path, width, height, duration_ms)

    async def _post_clip(self, image_url: str, prompt: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    self._endpoint_url,
                    json={"image_url": image_url, "prompt": prompt},
                    headers={"Authorization": f"Bearer {self._webhook_secret}"},
                )
        except httpx.TimeoutException as error:
            raise GenerationError(MODAL_TIMEOUT_MESSAGE) from error
        except httpx.HTTPError as error:
            raise GenerationError(MODAL_FAILURE_MESSAGE) from error
        if response.status_code != 200:
            logger.warning("modal endpoint returned HTTP %s", response.status_code)
            raise GenerationError(MODAL_FAILURE_MESSAGE)
        try:
            payload = response.json()
        except ValueError as error:
            raise GenerationError(MODAL_FAILURE_MESSAGE) from error
        if not isinstance(payload, dict):
            raise GenerationError(MODAL_FAILURE_MESSAGE)
        return cast(dict[str, Any], payload)


def _as_positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _parse_clip_payload(payload: dict[str, Any]) -> tuple[bytes, int, int, int]:
    raw_video = payload.get("video_base64")
    width = _as_positive_int(payload.get("width"))
    height = _as_positive_int(payload.get("height"))
    duration_ms = _as_positive_int(payload.get("duration_ms"))
    if not isinstance(raw_video, str) or width is None or height is None or duration_ms is None:
        raise GenerationError(MODAL_FAILURE_MESSAGE)
    try:
        video_bytes = base64.b64decode(raw_video, validate=True)
    except (binascii.Error, ValueError) as error:
        raise GenerationError(MODAL_FAILURE_MESSAGE) from error
    if not video_bytes:
        raise GenerationError(MODAL_FAILURE_MESSAGE)
    return video_bytes, width, height, duration_ms


async def _extract_poster(video_path: Path, poster_path: Path) -> None:
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video_path), "-frames:v", "1", "-q:v", "3", str(poster_path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        logger.warning("poster ffmpeg failed: %s", stderr.decode(errors="replace")[-500:])
        raise GenerationError(MODAL_FAILURE_MESSAGE)
