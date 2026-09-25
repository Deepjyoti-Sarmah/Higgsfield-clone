from pathlib import Path

import pytest

from app.adapters.stitch_filtergraph import build_stitch_command


def test_two_clips_with_cut_concat() -> None:
    argv, total = build_stitch_command(
        [Path("a.mp4"), Path("b.mp4")], [5.0, 4.0], ["cut", "cut"], None, Path("out.mp4")
    )

    assert total == 9.0
    joined = " ".join(argv)
    assert "concat=n=2:v=1:a=0" in joined
    assert "xfade" not in joined
    assert "-an" in argv
    assert argv[0] == "-i" and argv[-1] == "out.mp4"


def test_three_clips_offsets_and_total() -> None:
    argv, total = build_stitch_command(
        [Path("a.mp4"), Path("b.mp4"), Path("c.mp4")],
        [5.0, 5.0, 5.0],
        ["cut", "crossfade", "fade_black"],
        None,
        Path("out.mp4"),
    )

    assert total == 14.0
    joined = " ".join(argv)
    assert "xfade=transition=fade:duration=0.5:offset=4.5" in joined
    assert "xfade=transition=fadeblack:duration=0.5:offset=9.0" in joined


def test_audio_present_encodes_aac() -> None:
    argv, total = build_stitch_command(
        [Path("a.mp4"), Path("b.mp4")], [2.0, 2.0], ["cut", "crossfade"],
        Path("music.m4a"), Path("out.mp4"),
    )

    assert total == 3.5
    joined = " ".join(argv)
    assert "apad,atrim=0:3.5,afade=t=out:st=2.5:d=1.0" in joined
    assert "-an" not in argv
    assert "aac" in argv


def test_short_clip_raises() -> None:
    with pytest.raises(ValueError):
        build_stitch_command(
            [Path("a.mp4"), Path("b.mp4")], [0.5, 5.0], ["cut", "cut"], None, Path("out.mp4")
        )
