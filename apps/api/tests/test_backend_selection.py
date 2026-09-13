from pathlib import Path
from uuid import uuid4

import pytest

from app.adapters.backend_selection import select_model_adapter
from app.adapters.local_motion_adapter import LocalMotionAdapter
from app.adapters.mock_model_adapter import MockModelAdapter
from app.adapters.modal_adapter import ModalAdapter
from app.adapters.model_adapter import BackendNotConfiguredError, GenerationError, GenerationRequest
from app.adapters.openrouter_adapter import OpenRouterAdapter
from app.settings import Settings


def _request(work_dir: Path) -> GenerationRequest:
    return GenerationRequest(
        job_id=uuid4(),
        preset_slug="dolly-in",
        prompt=None,
        input_image_path=work_dir / "input.jpg",
        input_image_url="http://example.test/input.jpg",
        work_dir=work_dir,
    )


@pytest.mark.parametrize(
    ("backend", "expected"),
    [
        ("local-motion", LocalMotionAdapter),
        ("mock", MockModelAdapter),
        ("modal", ModalAdapter),
        ("openrouter", OpenRouterAdapter),
    ],
)
def test_selects_adapter_for_each_backend(backend: str, expected: type) -> None:
    adapter = select_model_adapter(Settings(generation_backend=backend))
    assert isinstance(adapter, expected)
    assert adapter.name == backend


async def test_mock_copies_fixtures(tmp_path: Path) -> None:
    adapter = select_model_adapter(Settings(generation_backend="mock"))
    result = await adapter.generate_video(_request(tmp_path))
    assert result.video_path.stat().st_size > 0
    assert result.poster_path.stat().st_size > 0
    assert (result.width, result.height) == (64, 64)
    assert result.duration_ms == 1000


async def test_mock_can_be_forced_to_fail(tmp_path: Path) -> None:
    adapter = select_model_adapter(Settings(generation_backend="mock", mock_generation_fails=True))
    with pytest.raises(GenerationError, match="Mock failure"):
        await adapter.generate_video(_request(tmp_path))


async def test_modal_without_endpoint_is_not_configured(tmp_path: Path) -> None:
    adapter = select_model_adapter(Settings(generation_backend="modal"))
    with pytest.raises(BackendNotConfiguredError, match="not configured"):
        await adapter.generate_video(_request(tmp_path))


async def test_modal_with_endpoint_reports_not_implemented(tmp_path: Path) -> None:
    adapter = select_model_adapter(
        Settings(generation_backend="modal", modal_endpoint_url="https://modal.example")
    )
    with pytest.raises(GenerationError, match="not implemented yet"):
        await adapter.generate_video(_request(tmp_path))


async def test_openrouter_without_key_is_not_configured(tmp_path: Path) -> None:
    adapter = select_model_adapter(Settings(generation_backend="openrouter"))
    with pytest.raises(BackendNotConfiguredError, match="not configured"):
        await adapter.generate_video(_request(tmp_path))


async def test_openrouter_with_key_reports_not_implemented(tmp_path: Path) -> None:
    adapter = select_model_adapter(
        Settings(generation_backend="openrouter", openrouter_api_key="sk-test")
    )
    with pytest.raises(GenerationError, match="not implemented yet"):
        await adapter.generate_video(_request(tmp_path))
