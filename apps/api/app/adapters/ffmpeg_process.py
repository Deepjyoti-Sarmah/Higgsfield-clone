import asyncio
import logging
from pathlib import Path

from app.adapters.model_adapter import GenerationError

logger = logging.getLogger(__name__)

RENDER_ERROR = "Render failed. Your credit was refunded."


class FfmpegError(GenerationError):
    """ffmpeg/ffprobe failed; str() is the internal stderr tail, user_message stays safe."""

    def __init__(self, detail: str) -> None:
        super().__init__(RENDER_ERROR)
        self.detail = detail

    def __str__(self) -> str:
        return self.detail


async def run_ffmpeg(args: list[str]) -> None:
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        tail = stderr.decode(errors="replace")[-2000:]
        logger.warning("ffmpeg exited %s: %s", process.returncode, tail)
        raise FfmpegError(f"ffmpeg exited {process.returncode}: {tail}")


async def probe_duration_seconds(path: Path) -> float:
    process = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
        str(path), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    try:
        return float(stdout.decode(errors="replace").strip())
    except ValueError as error:
        tail = stderr.decode(errors="replace")[-500:]
        raise FfmpegError(f"ffprobe failed for {path}: {tail}") from error
