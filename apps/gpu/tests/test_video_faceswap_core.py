"""T6b unit tests: sampling caps, faceless ratio, ffmpeg audio copy."""

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class _Any:
    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        return _Any()


def _install_remote_stubs() -> None:
    modal_stub = types.ModuleType("modal")
    modal_stub.__getattr__ = lambda name: _Any()  # type: ignore[attr-defined]
    fastapi_stub = types.ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = "") -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class Request:
        pass

    fastapi_stub.HTTPException = HTTPException  # type: ignore[attr-defined]
    fastapi_stub.Request = Request  # type: ignore[attr-defined]
    sys.modules.setdefault("modal", modal_stub)
    sys.modules.setdefault("fastapi", fastapi_stub)


_install_remote_stubs()

from video_face_swap import (  # noqa: E402
    FACELESS_RATIO_LIMIT,
    MAX_FPS,
    MAX_FRAMES,
    NO_FACE_VIDEO_MESSAGE,
    build_assemble_args,
    build_extract_args,
    check_faceless_ratio,
    plan_frame_sampling,
)

from face_swap_core import NO_FACE_IN_TARGET, NoFaceError  # noqa: E402


def test_sampling_caps_fps_at_ten_and_frames_at_300():
    assert plan_frame_sampling(30.0, 30.0) == (MAX_FPS, MAX_FRAMES)


def test_sampling_keeps_low_source_fps_unchanged():
    assert plan_frame_sampling(5.0, 5.0) == (5.0, 25)


def test_sampling_never_returns_zero_frames():
    assert plan_frame_sampling(0.0, 30.0)[1] == 1


def test_faceless_majority_raises_with_user_safe_message():
    with pytest.raises(NoFaceError, match=NO_FACE_VIDEO_MESSAGE):
        check_faceless_ratio(151, 300)


def test_exactly_half_faceless_passes():
    assert FACELESS_RATIO_LIMIT == 0.5
    check_faceless_ratio(150, 300)


def test_empty_video_raises_with_target_message():
    with pytest.raises(NoFaceError, match=NO_FACE_IN_TARGET):
        check_faceless_ratio(0, 0)


def test_assemble_args_copy_the_source_audio_track():
    args = build_assemble_args(Path("frame-%04d.png"), Path("target.mp4"),
                               Path("out.mp4"), 10.0)
    assert "-c:a" in args and args[args.index("-c:a") + 1] == "copy"
    assert "1:a?" in args


def test_extract_args_use_the_planned_frame_rate():
    args = build_extract_args(Path("target.mp4"), Path("frame-%04d.png"), 7.5)
    assert f"fps={7.5}" in args
