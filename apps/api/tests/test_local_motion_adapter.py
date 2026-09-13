import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from app.adapters.local_motion_adapter import LocalMotionAdapter
from app.adapters.model_adapter import GenerationError, GenerationRequest
from app.adapters.motion_recipes import FRAMES, MOTION_RECIPES
from app.domain.preset_catalog import PRESET_SLUGS

IMAGE_ERROR = "We couldn't animate this image. Try another one."
UNKNOWN_PRESET_ERROR = "This preset isn't available."


def _make_image(path: Path, size: str) -> Path:
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", f"testsrc2=size={size}",
            "-frames:v", "1", str(path),
        ],
        check=True,
    )
    return path


def _probe_video(path: Path) -> tuple[str, int, int, int]:
    output = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,nb_frames",
            "-of", "csv=p=0", str(path),
        ],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    codec, width, height, frames = output.split(",")
    return codec, int(width), int(height), int(frames)


def _duration_seconds(path: Path) -> float:
    output = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return float(output)


def _request(slug: str, image: Path, work_dir: Path) -> GenerationRequest:
    return GenerationRequest(uuid4(), slug, None, image, "http://example.test/input.jpg", work_dir)


@pytest.fixture(scope="module")
def landscape_image(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _make_image(tmp_path_factory.mktemp("images") / "landscape.jpg", "640x400")


@pytest.fixture(scope="module")
def portrait_image(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _make_image(tmp_path_factory.mktemp("images") / "portrait.png", "400x640")


def test_catalog_slugs_match_recipe_slugs() -> None:
    assert set(MOTION_RECIPES) == set(PRESET_SLUGS)
    assert len(MOTION_RECIPES) == 12


@pytest.mark.parametrize("slug", sorted(MOTION_RECIPES))
async def test_renders_every_preset(slug: str, landscape_image: Path, tmp_path: Path) -> None:
    result = await LocalMotionAdapter().generate_video(_request(slug, landscape_image, tmp_path))
    codec, width, height, frames = _probe_video(result.video_path)
    assert codec == "h264"
    assert width <= 1280 and height <= 720
    assert frames == FRAMES
    assert _duration_seconds(result.video_path) == pytest.approx(5.0, abs=0.05)
    data = result.video_path.read_bytes()
    assert data.index(b"moov") < data.index(b"mdat")
    assert result.poster_path.stat().st_size > 0
    assert (result.width, result.height) == (1280, 720)
    assert result.duration_ms == 5000


async def test_portrait_input_uses_portrait_canvas(portrait_image: Path, tmp_path: Path) -> None:
    result = await LocalMotionAdapter().generate_video(
        _request("dolly-in", portrait_image, tmp_path)
    )
    assert (result.width, result.height) == (720, 1280)
    _, width, height, frames = _probe_video(result.video_path)
    assert (width, height) == (720, 1280)
    assert frames == FRAMES


async def test_unknown_preset_raises(landscape_image: Path, tmp_path: Path) -> None:
    with pytest.raises(GenerationError) as error:
        await LocalMotionAdapter().generate_video(
            _request("not-a-preset", landscape_image, tmp_path)
        )
    assert error.value.user_message == UNKNOWN_PRESET_ERROR


async def test_corrupt_input_raises(tmp_path: Path) -> None:
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"this is not an image")
    with pytest.raises(GenerationError) as error:
        await LocalMotionAdapter().generate_video(
            _request("dolly-in", broken, tmp_path / "work")
        )
    assert error.value.user_message == IMAGE_ERROR
