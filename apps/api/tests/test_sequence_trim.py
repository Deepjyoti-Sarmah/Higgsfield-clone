import shutil
import subprocess
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.ffmpeg_stitcher import stitch_clips
from app.adapters.stitch_filtergraph import build_stitch_command
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.sequence_helpers import build_sequence_body, create_succeeded_clip

SessionMaker = async_sessionmaker[AsyncSession]


def test_trim_prefix_and_trimmed_lengths_drive_offsets() -> None:
    argv, total = build_stitch_command(
        [Path("a.mp4"), Path("b.mp4")], [2.0, 2.0], ["cut", "crossfade"],
        None, Path("out.mp4"), trims=[(500, 2500), (0, None)],
    )

    joined = " ".join(argv)
    assert "trim=start=0.5:end=2.5,setpts=PTS-STARTPTS" in joined
    assert "trim=start=0.0,setpts=PTS-STARTPTS" in joined
    assert total == 3.5


def test_trim_below_minimum_raises() -> None:
    with pytest.raises(ValueError):
        build_stitch_command(
            [Path("a.mp4"), Path("b.mp4")], [0.4, 2.0], ["cut", "cut"],
            None, Path("out.mp4"), trims=[(0, 400), (0, None)],
        )


requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")


def make_testsrc(path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24:duration=3",
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True,
    )


def probe_seconds(path: Path) -> float:
    done = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
         str(path)], check=True, capture_output=True, text=True,
    )
    return float(done.stdout.strip())


@requires_ffmpeg
async def test_trimmed_crossfade_output_duration(tmp_path: Path) -> None:
    first, second = tmp_path / "a.mp4", tmp_path / "b.mp4"
    make_testsrc(first)
    make_testsrc(second)
    result = await stitch_clips(
        [first, second], ["cut", "crossfade"], None, tmp_path,
        trims=[(500, 2500), (500, 2500)],
    )

    duration = probe_seconds(result.video_path)
    assert abs(duration - 3.5) < 0.15
    assert abs(result.duration_ms - 3500) < 150


async def test_start_at_or_after_end_is_422(guest_client: AsyncClient) -> None:
    created = await guest_client.post("/api/v1/sequence-jobs", json={
        "clips": [
            {"job_id": "00000000-0000-0000-0000-000000000001",
             "trim_start_ms": 1000, "trim_end_ms": 1000},
            {"job_id": "00000000-0000-0000-0000-000000000002"},
        ],
        "idempotency_key": "t0106-seq-01",
    })
    assert created.status_code == 422


async def test_create_and_read_round_trip_echoes_trim(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    first = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0106-aa")
    second = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0106-bb")
    body = build_sequence_body([first, second], "t0106-seq-02")
    body["clips"][1]["trim_start_ms"] = 250
    body["clips"][1]["trim_end_ms"] = 2750

    created = await guest_client.post("/api/v1/sequence-jobs", json=body)
    assert created.status_code == 202
    read = await guest_client.get(f"/api/v1/sequence-jobs/{created.json()['id']}")

    assert read.status_code == 200
    clips = read.json()["clips"]
    assert (clips[0]["trim_start_ms"], clips[0]["trim_end_ms"]) == (0, None)
    assert (clips[1]["trim_start_ms"], clips[1]["trim_end_ms"]) == (250, 2750)
