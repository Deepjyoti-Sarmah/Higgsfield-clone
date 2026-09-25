from dataclasses import dataclass
from pathlib import Path

from app.adapters.ffmpeg_process import probe_duration_seconds, run_ffmpeg
from app.adapters.stitch_filtergraph import build_stitch_command
from app.domain.sequence_rules import POSTER_AT_SECONDS


@dataclass(frozen=True)
class StitchResult:
    video_path: Path
    poster_path: Path
    duration_ms: int


async def stitch_clips(
    clip_paths: list[Path],
    transitions: list[str],
    audio_path: Path | None,
    work_dir: Path,
) -> StitchResult:
    seconds = [await probe_duration_seconds(path) for path in clip_paths]
    video_path = work_dir / "video.mp4"
    argv, total = build_stitch_command(clip_paths, seconds, transitions, audio_path, video_path)
    await run_ffmpeg(argv)
    poster_path = work_dir / "poster.jpg"
    await run_ffmpeg([
        "-ss", str(min(POSTER_AT_SECONDS, total / 2)),
        "-i", str(video_path),
        "-frames:v", "1",
        str(poster_path),
    ])
    return StitchResult(video_path, poster_path, int(total * 1000))
