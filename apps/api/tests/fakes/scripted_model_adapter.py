import asyncio
from pathlib import Path
from typing import Literal

from app.adapters.model_adapter import GenerationError, GenerationRequest, GenerationResult

Outcome = Literal["success", "generation_error", "runtime_error", "hang"]

TINY_VIDEO = b"\x00\x00\x00\x18ftypmp42" + b"tiny-video"
TINY_POSTER = b"\xff\xd8\xff" + b"tiny-poster"
VIDEO_SIZE = len(TINY_VIDEO)
POSTER_SIZE = len(TINY_POSTER)


class ScriptedModelAdapter:
    name = "scripted"

    def __init__(self, outcome: Outcome = "success", user_message: str = "Nope") -> None:
        self.outcome = outcome
        self.user_message = user_message

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        if self.outcome == "hang":
            await asyncio.sleep(3600)
        if self.outcome == "generation_error":
            raise GenerationError(self.user_message)
        if self.outcome == "runtime_error":
            raise RuntimeError("kaboom-secret")
        return self.write_tiny_outputs(request.work_dir)

    def write_tiny_outputs(self, work_dir: Path) -> GenerationResult:
        work_dir.mkdir(parents=True, exist_ok=True)
        video_path = work_dir / "video.mp4"
        poster_path = work_dir / "poster.jpg"
        video_path.write_bytes(TINY_VIDEO)
        poster_path.write_bytes(TINY_POSTER)
        return GenerationResult(video_path, poster_path, 64, 64, 1000)
