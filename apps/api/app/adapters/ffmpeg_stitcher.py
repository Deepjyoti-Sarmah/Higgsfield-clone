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


def _trimmed_seconds(
    durations: list[float], trims: list[tuple[int, int | None]] | None
) -> list[float]:
    if trims is None:
        return durations
    lengths = []
    for duration, (start_ms, end_ms) in zip(durations, trims, strict=True):
        end_seconds = min(end_ms / 1000, duration) if end_ms is not None else duration
        lengths.append(end_seconds - start_ms / 1000)
    return lengths


async def stitch_clips(
    clip_paths: list[Path],
    transitions: list[str],
    audio_path: Path | None,
    work_dir: Path,
    trims: list[tuple[int, int | None]] | None = None,
) -> StitchResult:
    durations = [await probe_duration_seconds(path) for path in clip_paths]
    seconds = _trimmed_seconds(durations, trims)
    video_path = work_dir / "video.mp4"
    argv, total = build_stitch_command(
        clip_paths, seconds, transitions, audio_path, video_path, trims
    )
    await run_ffmpeg(argv)
    poster_path = work_dir / "poster.jpg"
    await run_ffmpeg([
        "-ss", str(min(POSTER_AT_SECONDS, total / 2)),
        "-i", str(video_path),
        "-frames:v", "1",
        str(poster_path),
    ])
    return StitchResult(video_path, poster_path, int(total * 1000))
