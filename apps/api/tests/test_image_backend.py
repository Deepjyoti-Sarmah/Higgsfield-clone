import struct
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.adapters.backend_selection import select_image_adapter
from app.adapters.image_model_adapter import ImageGenerationRequest
from app.adapters.model_adapter import BackendNotConfiguredError
from app.adapters.placeholder_image_adapter import (
    PlaceholderImageAdapter,
    UnconfiguredImageAdapter,
)
from app.adapters.png_placeholder import write_placeholder_png
from app.domain.image_rules import IMAGE_PIXEL_SIZES
from app.settings import Settings

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _request(
    work_dir: Path, job_id: UUID | None = None, aspect_ratio: str = "16:9", count: int = 2
) -> ImageGenerationRequest:
    return ImageGenerationRequest(
        job_id=job_id or uuid4(),
        prompt="a cat on a skateboard",
        aspect_ratio=aspect_ratio,
        quality="standard",
        count=count,
        work_dir=work_dir,
    )


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == PNG_SIGNATURE
    assert data[12:16] == b"IHDR"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def test_the_writer_is_deterministic_and_seed_sensitive(tmp_path: Path) -> None:
    first, second, other = (tmp_path / name for name in ("a.png", "b.png", "c.png"))

    write_placeholder_png(first, 64, 48, 7)
    write_placeholder_png(second, 64, 48, 7)
    write_placeholder_png(other, 64, 48, 8)

    assert _png_size(first) == (64, 48)
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes() != other.read_bytes()


async def test_the_adapter_writes_one_real_png_per_image(tmp_path: Path) -> None:
    adapter = PlaceholderImageAdapter("local-motion")

    result = await adapter.generate_image(_request(tmp_path, aspect_ratio="16:9", count=2))

    assert adapter.name == "local-motion"
    assert [path.name for path in result.image_paths] == ["image-1.png", "image-2.png"]
    assert (result.width, result.height) == IMAGE_PIXEL_SIZES["16:9"]
    for path in result.image_paths:
        assert _png_size(path) == IMAGE_PIXEL_SIZES["16:9"]


@pytest.mark.parametrize("aspect_ratio", ["1:1", "4:5", "3:2", "16:9", "9:16"])
async def test_every_aspect_ratio_gets_its_own_dimensions(
    tmp_path: Path, aspect_ratio: str
) -> None:
    adapter = PlaceholderImageAdapter("mock")

    result = await adapter.generate_image(_request(tmp_path, aspect_ratio=aspect_ratio, count=1))

    assert _png_size(result.image_paths[0]) == IMAGE_PIXEL_SIZES[aspect_ratio]


async def test_the_same_job_id_renders_identical_bytes(tmp_path: Path) -> None:
    job_id = uuid4()

    first = await PlaceholderImageAdapter("mock").generate_image(_request(tmp_path / "a", job_id))
    second = await PlaceholderImageAdapter("mock").generate_image(_request(tmp_path / "b", job_id))

    assert first.image_paths[0].read_bytes() == second.image_paths[0].read_bytes()


@pytest.mark.parametrize(
    ("backend", "expected"),
    [
        ("local-motion", PlaceholderImageAdapter),
        ("mock", PlaceholderImageAdapter),
        ("modal", UnconfiguredImageAdapter),
        ("openrouter", UnconfiguredImageAdapter),
    ],
)
def test_selects_an_image_adapter_per_backend(backend: str, expected: type) -> None:
    adapter = select_image_adapter(Settings(generation_backend=backend))

    assert isinstance(adapter, expected)
    assert adapter.name == backend


@pytest.mark.parametrize("backend", ["modal", "openrouter"])
async def test_unconfigured_backends_fail_loudly(tmp_path: Path, backend: str) -> None:
    adapter = select_image_adapter(Settings(generation_backend=backend))

    with pytest.raises(BackendNotConfiguredError, match="not configured"):
        await adapter.generate_image(_request(tmp_path))
