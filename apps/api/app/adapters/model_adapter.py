import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class GenerationRequest:
    job_id: uuid.UUID | None
    preset_slug: str
    prompt: str | None
    input_image_path: Path
    input_image_url: str
    work_dir: Path


@dataclass(frozen=True)
class GenerationResult:
    video_path: Path
    poster_path: Path
    width: int
    height: int
    duration_ms: int


class GenerationError(Exception):
    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


class BackendNotConfiguredError(GenerationError): ...


class ModelAdapter(Protocol):
    name: str

    async def generate_video(self, request: GenerationRequest) -> GenerationResult: ...
