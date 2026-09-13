import asyncio
import shutil
from pathlib import Path

from app.adapters.model_adapter import GenerationError, GenerationRequest, GenerationResult
from app.settings import Settings

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MOCK_WIDTH = 64
MOCK_HEIGHT = 64
MOCK_DURATION_MS = 1000


class MockModelAdapter:
    name = "mock"

    def __init__(self, settings: Settings) -> None:
        self._fails = settings.mock_generation_fails

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        if self._fails:
            raise GenerationError("Mock failure")
        request.work_dir.mkdir(parents=True, exist_ok=True)
        video_path = request.work_dir / "video.mp4"
        poster_path = request.work_dir / "poster.jpg"
        await asyncio.to_thread(shutil.copyfile, FIXTURES_DIR / "mock-video.mp4", video_path)
        await asyncio.to_thread(shutil.copyfile, FIXTURES_DIR / "mock-poster.jpg", poster_path)
        return GenerationResult(video_path, poster_path, MOCK_WIDTH, MOCK_HEIGHT, MOCK_DURATION_MS)
