import asyncio
import uuid
from pathlib import Path

from app.adapters.image_model_adapter import ImageGenerationRequest, ImageGenerationResult
from app.adapters.model_adapter import BackendNotConfiguredError
from app.adapters.png_placeholder import write_placeholder_png
from app.domain.image_rules import IMAGE_PIXEL_SIZES

DEFAULT_PIXEL_SIZE = (512, 512)


def _size_for(aspect_ratio: str) -> tuple[int, int]:
    for ratio, size in IMAGE_PIXEL_SIZES.items():
        if ratio == aspect_ratio:
            return size
    return DEFAULT_PIXEL_SIZE


def _seed_for(job_id: uuid.UUID, position: int) -> int:
    return (job_id.int + position * 31) % 997


class PlaceholderImageAdapter:
    """A runnable image backend: real PNG files, obviously placeholder content."""

    def __init__(self, name: str) -> None:
        self.name = name

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        request.work_dir.mkdir(parents=True, exist_ok=True)
        width, height = _size_for(request.aspect_ratio)
        paths: list[Path] = []
        for position in range(1, request.count + 1):
            path = request.work_dir / f"image-{position}.png"
            seed = _seed_for(request.job_id, position)
            await asyncio.to_thread(write_placeholder_png, path, width, height, seed)
            paths.append(path)
        return ImageGenerationResult(image_paths=paths, width=width, height=height)


class UnconfiguredImageAdapter:
    """No image model is wired for this backend; fail loudly so the job refunds."""

    def __init__(self, name: str) -> None:
        self.name = name

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        raise BackendNotConfiguredError(
            f"Image generation is not configured (backend={self.name})"
        )
