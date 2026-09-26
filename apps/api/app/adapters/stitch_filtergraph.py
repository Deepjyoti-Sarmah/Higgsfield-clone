from pathlib import Path

from app.domain.sequence_rules import (
    MIN_TRIMMED_SECONDS,
    MUSIC_FADE_SECONDS,
    OUTPUT_FPS,
    OUTPUT_HEIGHT,
    OUTPUT_WIDTH,
    TRANSITION_SECONDS,
)

NORMALISE_CHAIN = (
    f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
    f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
    f"setsar=1,fps={OUTPUT_FPS},format=yuv420p,settb=AVTB"
)


def _trim_prefix(start_ms: int, end_ms: int | None) -> str:
    start = start_ms / 1000
    if end_ms is None:
        return f"trim=start={start},setpts=PTS-STARTPTS,"
    return f"trim=start={start}:end={end_ms / 1000},setpts=PTS-STARTPTS,"


def _fold_segment(
    filters: list[str], previous: str, index: int, transition: str,
    seconds: float, total: float,
) -> tuple[str, float]:
    outgoing = f"[x{index}]"
    if transition == "cut":
        filters.append(f"{previous}[v{index}]concat=n=2:v=1:a=0{outgoing}")
        return outgoing, total + seconds
    kind = "fade" if transition == "crossfade" else "fadeblack"
    offset = total - TRANSITION_SECONDS
    filters.append(
        f"{previous}[v{index}]xfade=transition={kind}"
        f":duration={TRANSITION_SECONDS}:offset={offset}{outgoing}"
    )
    return outgoing, total + seconds - TRANSITION_SECONDS


def build_stitch_command(
    clip_paths: list[Path],
    clip_seconds: list[float],
    transitions: list[str],
    audio_path: Path | None,
    output_path: Path,
    trims: list[tuple[int, int | None]] | None = None,
) -> tuple[list[str], float]:
    if any(length < MIN_TRIMMED_SECONDS for length in clip_seconds):
        raise ValueError(f"clips must be at least {MIN_TRIMMED_SECONDS} s long")
    argv: list[str] = []
    for clip in clip_paths:
        argv += ["-i", str(clip)]
    if audio_path is not None:
        argv += ["-i", str(audio_path)]
    filters: list[str] = []
    for index in range(len(clip_paths)):
        trim = _trim_prefix(*trims[index]) if trims is not None else ""
        filters.append(f"[{index}:v]{trim}{NORMALISE_CHAIN}[v{index}]")
    previous = "[v0]"
    total = clip_seconds[0]
    for index in range(1, len(clip_paths)):
        previous, total = _fold_segment(
            filters, previous, index, transitions[index], clip_seconds[index], total
        )
    if audio_path is not None:
        filters.append(
            f"[{len(clip_paths)}:a]apad,atrim=0:{total},"
            f"afade=t=out:st={total - MUSIC_FADE_SECONDS}:d={MUSIC_FADE_SECONDS}[aout]"
        )
    argv += ["-filter_complex", ";".join(filters), "-map", previous]
    if audio_path is not None:
        argv += ["-map", "[aout]", "-c:a", "aac"]
    else:
        argv += ["-an"]
    argv += ["-c:v", "libx264", "-crf", "23", "-preset", "veryfast", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", str(output_path)]
    return argv, total
