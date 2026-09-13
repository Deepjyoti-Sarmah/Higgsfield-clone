import base64
import binascii
import logging
from typing import Any, cast

import httpx

from app.adapters.image_model_adapter import ImageGenerationRequest, ImageGenerationResult
from app.adapters.model_adapter import BackendNotConfiguredError, GenerationError
from app.adapters.placeholder_image_adapter import PlaceholderImageAdapter
from app.domain.image_dimensions import FLUX_PIXEL_SIZES, steps_for_quality
from app.domain.image_rules import ImageAspectRatio, ImageQuality
from app.settings import Settings

logger = logging.getLogger(__name__)

IMAGE_PREFIX = "image"
IMAGE_SUFFIX = ".png"
MODAL_FAILURE_MESSAGE = "The AI image backend failed. Your credits were refunded."
MODAL_TIMEOUT_MESSAGE = "The AI image backend timed out. Your credits were refunded."


class ModalImageAdapter:
    name = "modal"

    def __init__(self, settings: Settings) -> None:
        self._endpoint_url = settings.modal_image_endpoint_url
        self._webhook_secret = settings.modal_webhook_secret
        self._timeout_seconds = settings.generation_timeout_seconds

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self._endpoint_url:
            raise BackendNotConfiguredError(
                "modal image backend not configured: set MODAL_IMAGE_ENDPOINT_URL"
            )
        aspect_ratio = cast(ImageAspectRatio, request.aspect_ratio)
        quality = cast(ImageQuality, request.quality)
        width, height = FLUX_PIXEL_SIZES[aspect_ratio]
        payload = await self._post_images(request, width, height, quality)
        images = _parse_images(payload)
        if len(images) != request.count:
            raise GenerationError(MODAL_FAILURE_MESSAGE)
        request.work_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for position, data in enumerate(images, start=1):
            path = request.work_dir / f"{IMAGE_PREFIX}-{position}{IMAGE_SUFFIX}"
            path.write_bytes(data)
            paths.append(path)
        return ImageGenerationResult(image_paths=paths, width=width, height=height)

    async def _post_images(
        self, request: ImageGenerationRequest, width: int, height: int, quality: ImageQuality
    ) -> dict[str, Any]:
        body = {
            "prompt": request.prompt,
            "width": width,
            "height": height,
            "steps": steps_for_quality(quality),
            "count": request.count,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    self._endpoint_url,
                    json=body,
                    headers={"Authorization": f"Bearer {self._webhook_secret}"},
                )
        except httpx.TimeoutException as error:
            raise GenerationError(MODAL_TIMEOUT_MESSAGE) from error
        except httpx.HTTPError as error:
            raise GenerationError(MODAL_FAILURE_MESSAGE) from error
        if response.status_code != 200:
            logger.warning("modal image endpoint returned HTTP %s", response.status_code)
            raise GenerationError(MODAL_FAILURE_MESSAGE)
        try:
            payload = response.json()
        except ValueError as error:
            raise GenerationError(MODAL_FAILURE_MESSAGE) from error
        if not isinstance(payload, dict):
            raise GenerationError(MODAL_FAILURE_MESSAGE)
        return cast(dict[str, Any], payload)


def _parse_images(payload: dict[str, Any]) -> list[bytes]:
    raw_images = payload.get("images_base64")
    if not isinstance(raw_images, list) or not raw_images:
        raise GenerationError(MODAL_FAILURE_MESSAGE)
    images: list[bytes] = []
    for raw_image in raw_images:
        if not isinstance(raw_image, str):
            raise GenerationError(MODAL_FAILURE_MESSAGE)
        try:
            data = base64.b64decode(raw_image, validate=True)
        except (binascii.Error, ValueError) as error:
            raise GenerationError(MODAL_FAILURE_MESSAGE) from error
        if not data:
            raise GenerationError(MODAL_FAILURE_MESSAGE)
        images.append(data)
    return images


class FallbackImageAdapter:
    """Paid image backend first, placeholder second; `name` reports which one ran."""

    def __init__(self, primary: ModalImageAdapter, fallback: PlaceholderImageAdapter) -> None:
        self._primary = primary
        self._fallback = fallback
        self.name = primary.name

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        try:
            result = await self._primary.generate_image(request)
        except (GenerationError, TimeoutError):
            logger.warning("modal image backend failed; falling back to the placeholder")
            self.name = self._fallback.name
            return await self._fallback.generate_image(request)
        self.name = self._primary.name
        return result
