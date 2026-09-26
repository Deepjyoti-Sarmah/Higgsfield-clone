import base64
import binascii
import logging
from typing import Any, Protocol, cast

import httpx

from app.adapters.model_adapter import BackendNotConfiguredError, GenerationError
from app.domain.faceswap_rules import FACESWAP_BACKEND
from app.settings import Settings

logger = logging.getLogger(__name__)

FAILURE_MESSAGE = "The AI face swap backend failed. Your credits were refunded."
TIMEOUT_MESSAGE = "The AI face swap backend timed out. Your credits were refunded."


class FaceSwapAdapterProtocol(Protocol):
    name: str

    async def swap(self, source_url: str, target_url: str) -> bytes: ...


class FaceSwapAdapter:
    name = FACESWAP_BACKEND

    def __init__(self, settings: Settings) -> None:
        self._endpoint_url = settings.modal_faceswap_endpoint_url
        self._webhook_secret = settings.modal_webhook_secret
        self._timeout_seconds = settings.generation_timeout_seconds

    async def swap(self, source_url: str, target_url: str) -> bytes:
        if not self._endpoint_url:
            raise BackendNotConfiguredError(
                "modal faceswap backend not configured: set MODAL_FACESWAP_ENDPOINT_URL"
            )
        response = await self._post(source_url, target_url)
        if response.status_code == 422:
            raise GenerationError(_error_detail(response))
        if response.status_code != 200:
            logger.warning("modal faceswap endpoint returned HTTP %s", response.status_code)
            raise GenerationError(FAILURE_MESSAGE)
        return _parse_image(response)

    async def _post(self, source_url: str, target_url: str) -> httpx.Response:
        body = {"source_url": source_url, "target_url": target_url}
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                return await client.post(
                    self._endpoint_url,
                    json=body,
                    headers={"Authorization": f"Bearer {self._webhook_secret}"},
                )
        except httpx.TimeoutException as error:
            raise GenerationError(TIMEOUT_MESSAGE) from error
        except httpx.HTTPError as error:
            raise GenerationError(FAILURE_MESSAGE) from error


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return FAILURE_MESSAGE
    if isinstance(payload, dict) and isinstance(payload.get("detail"), str):
        return cast(str, payload["detail"])
    return FAILURE_MESSAGE


def _parse_image(response: httpx.Response) -> bytes:
    try:
        payload: Any = response.json()
    except ValueError as error:
        raise GenerationError(FAILURE_MESSAGE) from error
    if not isinstance(payload, dict):
        raise GenerationError(FAILURE_MESSAGE)
    raw = payload.get("image_base64")
    if not isinstance(raw, str) or not raw:
        raise GenerationError(FAILURE_MESSAGE)
    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as error:
        raise GenerationError(FAILURE_MESSAGE) from error
    if not data:
        raise GenerationError(FAILURE_MESSAGE)
    return data
