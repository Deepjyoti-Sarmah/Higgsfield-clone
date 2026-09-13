import asyncio
import logging
from pathlib import Path

from app.adapters.model_adapter import GenerationError, GenerationRequest, GenerationResult
from app.adapters.motion_recipes import FPS, FRAMES, MOTION_RECIPES, build_motion_filter, pick_canvas

logger = logging.getLogger(__name__)

DURATION_MS = 5000
IMAGE_ERROR = "We couldn't animate this image. Try another one."


class LocalMotionAdapter:
    name = "local-motion"

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        recipe = MOTION_RECIPES.get(request.preset_slug)
        if recipe is None:
            raise GenerationError("This preset isn't available.")
        request.work_dir.mkdir(parents=True, exist_ok=True)
        input_width, input_height = await self._input_size(request.input_image_path)
        width, height = pick_canvas(input_width, input_height)
        video_path = request.work_dir / "video.mp4"
        poster_path = request.work_dir / "poster.jpg"
        await self._run_ffmpeg(
            "-i", str(request.input_image_path),
            "-vf", build_motion_filter(recipe, width, height),
            "-frames:v", str(FRAMES), "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(video_path),
        )
        await self._run_ffmpeg("-i", str(video_path), "-frames:v", "1", "-q:v", "3", str(poster_path))
        return GenerationResult(video_path, poster_path, width, height, DURATION_MS)

    async def _input_size(self, image_path: Path) -> tuple[int, int]:
        code, stdout, stderr = await _run(
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0", str(image_path),
        )
        if code != 0:
            _log_failure("ffprobe", code, stderr)
            raise GenerationError(IMAGE_ERROR)
        parts = stdout.decode(errors="replace").strip().split(",")
        if len(parts) < 2:
            raise GenerationError(IMAGE_ERROR)
        try:
            width, height = int(parts[0]), int(parts[1])
        except ValueError as error:
            raise GenerationError(IMAGE_ERROR) from error
        if width <= 0 or height <= 0:
            raise GenerationError(IMAGE_ERROR)
        return width, height

    async def _run_ffmpeg(self, *arguments: str) -> None:
        code, _, stderr = await _run("ffmpeg", "-y", "-loglevel", "error", *arguments)
        if code != 0:
            _log_failure("ffmpeg", code, stderr)
            raise GenerationError(IMAGE_ERROR)


async def _run(*command: str) -> tuple[int, bytes, bytes]:
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (-1 if process.returncode is None else process.returncode), stdout, stderr


def _log_failure(tool: str, code: int, stderr: bytes) -> None:
    logger.warning("%s exited %s: %s", tool, code, stderr.decode(errors="replace")[-2000:])
