import base64
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import pytest

from app.adapters.image_model_adapter import ImageGenerationRequest
from app.adapters.modal_image_adapter import ModalImageAdapter
from app.adapters.model_adapter import BackendNotConfiguredError, GenerationError
from app.adapters.png_placeholder import write_placeholder_png
from app.domain.image_dimensions import FLUX_PIXEL_SIZES
from app.domain.image_rules import ASPECT_RATIOS
from app.settings import Settings

ENDPOINT = "https://modal.example/image"
PROMPT = "a neon-lit tokyo alley at night"


def _request(
    work_dir: Path, *, aspect_ratio: str = "16:9", quality: str = "standard", count: int = 2
) -> ImageGenerationRequest:
    return ImageGenerationRequest(
        job_id=uuid4(),
        prompt=PROMPT,
        aspect_ratio=aspect_ratio,
        quality=quality,
        count=count,
        work_dir=work_dir,
    )


def _settings(endpoint: str = ENDPOINT) -> Settings:
    return Settings(
        image_generation_backend="modal",
        modal_image_endpoint_url=endpoint,
        modal_webhook_secret="wh-test",
    )


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _client_class(seen: list[dict[str, Any]], response: Any = None, error: Any = None):
    class _FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            return None

        async def __aenter__(self) -> "_FakeClient":
            return self

        async def __aexit__(self, *args: Any) -> bool:
            return False

        async def post(self, url: str, json: Any = None, headers: Any = None) -> _FakeResponse:
            seen.append({"url": url, "json": json, "headers": headers})
            if error is not None:
                raise error
            return _FakeResponse(200, response)

    return _FakeClient


def _png_bytes(tmp_path: Path) -> bytes:
    path = tmp_path / "source.png"
    write_placeholder_png(path, 64, 64, 3)
    return path.read_bytes()


def _payload(images: list[bytes], width: int = 1344, height: int = 768) -> dict[str, Any]:
    return {
        "images_base64": [base64.b64encode(image).decode("ascii") for image in images],
        "width": width,
        "height": height,
    }


async def test_missing_endpoint_is_not_configured(tmp_path: Path) -> None:
    adapter = ModalImageAdapter(Settings(image_generation_backend="modal"))

    with pytest.raises(BackendNotConfiguredError, match="not configured"):
        await adapter.generate_image(_request(tmp_path))


async def test_success_writes_one_png_per_image_with_auth_and_params(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    png = _png_bytes(tmp_path)
    seen: list[dict[str, Any]] = []
    monkeypatch.setattr(httpx, "AsyncClient", _client_class(seen, _payload([png, png])))

    result = await ModalImageAdapter(_settings()).generate_image(
        _request(tmp_path, aspect_ratio="16:9", count=2)
    )

    assert [path.name for path in result.image_paths] == ["image-1.png", "image-2.png"]
    assert (result.width, result.height) == FLUX_PIXEL_SIZES["16:9"]
    assert result.image_paths[0].read_bytes() == png
    assert seen[0]["json"] == {
        "prompt": PROMPT,
        "width": 1344,
        "height": 768,
        "steps": 4,
        "count": 2,
    }
    assert seen[0]["headers"] == {"Authorization": "Bearer wh-test"}


@pytest.mark.parametrize("aspect_ratio", ASPECT_RATIOS)
async def test_every_aspect_ratio_maps_to_the_flux_geometry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aspect_ratio: str
) -> None:
    png = _png_bytes(tmp_path)
    seen: list[dict[str, Any]] = []
    monkeypatch.setattr(httpx, "AsyncClient", _client_class(seen, _payload([png])))

    result = await ModalImageAdapter(_settings()).generate_image(
        _request(tmp_path, aspect_ratio=aspect_ratio, count=1)
    )

    assert (result.width, result.height) == FLUX_PIXEL_SIZES[aspect_ratio]
    assert seen[0]["json"]["width"] == FLUX_PIXEL_SIZES[aspect_ratio][0]
    assert seen[0]["json"]["height"] == FLUX_PIXEL_SIZES[aspect_ratio][1]


async def test_high_quality_uses_eight_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    png = _png_bytes(tmp_path)
    seen: list[dict[str, Any]] = []
    monkeypatch.setattr(httpx, "AsyncClient", _client_class(seen, _payload([png])))

    await ModalImageAdapter(_settings()).generate_image(
        _request(tmp_path, quality="high", count=1)
    )

    assert seen[0]["json"]["steps"] == 8


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"images_base64": []},
        {"images_base64": "not-a-list"},
        {"images_base64": ["!!!"]},
        {"images_base64": ["eA==", 5]},
        ["not-a-dict"],
    ],
    ids=["empty", "empty-list", "not-a-list", "bad-base64", "non-string", "list-body"],
)
async def test_malformed_responses_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: Any
) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", _client_class([], payload))

    with pytest.raises(GenerationError, match="refunded"):
        await ModalImageAdapter(_settings()).generate_image(_request(tmp_path))


async def test_http_error_and_timeout_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _ErrorClient(_client_class([])):
        async def post(self, url: str, json: Any = None, headers: Any = None) -> _FakeResponse:
            return _FakeResponse(500, {})

    monkeypatch.setattr(httpx, "AsyncClient", _ErrorClient)
    with pytest.raises(GenerationError, match="refunded"):
        await ModalImageAdapter(_settings()).generate_image(_request(tmp_path))

    monkeypatch.setattr(
        httpx, "AsyncClient", _client_class([], error=httpx.TimeoutException("t"))
    )
    with pytest.raises(GenerationError, match="timed out"):
        await ModalImageAdapter(_settings()).generate_image(_request(tmp_path))
