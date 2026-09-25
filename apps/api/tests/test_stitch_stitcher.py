import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from app.adapters.ffmpeg_stitcher import stitch_clips

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")


def run_tool(*args: str) -> None:
    subprocess.run(list(args), check=True, capture_output=True)


def make_clip(path: Path, size: str) -> None:
    run_tool("ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=24:duration=2",
             "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(path))


def make_tone(path: Path, seconds: int) -> None:
    run_tool("ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
             "-c:a", "aac", str(path))


def probe_media(path: Path) -> dict[str, object]:
    done = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_entries", "format=duration",
         "-of", "json", str(path)], check=True, capture_output=True, text=True,
    )
    return json.loads(done.stdout)


def stream_facts(media: dict[str, object]) -> tuple[int, int, str, float, int]:
    streams = cast(list[dict[str, Any]], media["streams"])
    video = [s for s in streams if s["codec_type"] == "video"][0]
    audios = [s for s in streams if s["codec_type"] == "audio"]
    duration = float(cast(dict[str, Any], media["format"])["duration"])
    return (int(video["width"]), int(video["height"]), str(video["r_frame_rate"]),
            duration, len(audios))


@pytest.fixture
def media_dir(tmp_path: Path) -> dict[str, Path]:
    narrow = tmp_path / "clip-narrow.mp4"
    tall = tmp_path / "clip-tall.mp4"
    make_clip(narrow, "960x544")
    make_clip(tall, "720x1280")
    short_tone = tmp_path / "tone-short.m4a"
    long_tone = tmp_path / "tone-long.m4a"
    make_tone(short_tone, 1)
    make_tone(long_tone, 10)
    return {"narrow": narrow, "tall": tall, "short": short_tone, "long": long_tone}


async def test_crossfade_output_shape(tmp_path: Path, media_dir: dict[str, Path]) -> None:
    result = await stitch_clips(
        [media_dir["narrow"], media_dir["tall"]], ["cut", "crossfade"], None, tmp_path
    )

    width, height, fps, duration, audios = stream_facts(probe_media(result.video_path))
    assert (width, height, fps, audios) == (1280, 720, "24/1", 0)
    assert abs(duration - 3.5) < 0.15
    assert abs(result.duration_ms - 3500) < 150
    assert result.poster_path.is_file()


async def test_short_audio_pads_to_video_length(
    tmp_path: Path, media_dir: dict[str, Path]
) -> None:
    result = await stitch_clips(
        [media_dir["narrow"], media_dir["tall"]], ["cut", "crossfade"],
        media_dir["short"], tmp_path,
    )

    _, _, _, duration, audios = stream_facts(probe_media(result.video_path))
    assert audios == 1
    assert abs(duration - 3.5) < 0.15


async def test_no_audio_leaves_silence_out(tmp_path: Path, media_dir: dict[str, Path]) -> None:
    result = await stitch_clips(
        [media_dir["narrow"], media_dir["tall"]], ["cut", "cut"], None, tmp_path
    )

    _, _, _, duration, audios = stream_facts(probe_media(result.video_path))
    assert audios == 0
    assert abs(duration - 4.0) < 0.15
