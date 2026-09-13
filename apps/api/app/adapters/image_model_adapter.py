import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ImageGenerationRequest:
    job_id: uuid.UUID
    prompt: str
    aspect_ratio: str
    quality: str
    count: int
    work_dir: Path


@dataclass(frozen=True)
class ImageGenerationResult:
    image_paths: list[Path]
    width: int
    height: int


class ImageModelAdapter(Protocol):
    name: str

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult: ...
