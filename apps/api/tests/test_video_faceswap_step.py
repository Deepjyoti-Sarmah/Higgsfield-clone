import subprocess
import uuid
from pathlib import Path

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.mock_model_adapter import MockModelAdapter
from app.adapters.model_adapter import GenerationError
from app.adapters.placeholder_image_adapter import PlaceholderImageAdapter
from app.adapters.video_face_swap_adapter import VideoFaceSwapAdapter
from app.domain.video_faceswap_rules import video_faceswap_cost
from app.models.asset import Asset
from app.models.job import Job
from app.repositories.job_steps import claim_next_queued_step
from app.services.generation_runs import RunSettings
from app.services.step_claiming import claim_step
from app.settings import Settings
from app.worker import run_claimed_step_for_kind
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import (
    GUEST_GRANT,
    balance_of,
    create_ready_asset,
    current_user_id,
)

SessionMaker = async_sessionmaker[AsyncSession]
WORKER_ID = "video-faceswap-test-worker"
DRAIN_WORKER = "video-faceswap-drain-worker"
RUN_SETTINGS = RunSettings(
    lease_seconds=300, generation_timeout_seconds=60.0, download_url_ttl_seconds=900
)
TARGET_DURATION_MS = 5000
TARGET_COST = video_faceswap_cost(TARGET_DURATION_MS)
NO_FACE_MESSAGE = "No face found in over half of the video frames"


class _FakeVideoFaceSwapAdapter:
    def __init__(self, video_bytes: bytes | None = None, error: str | None = None):
        self.name = "modal-video-faceswap"
        self._video_bytes = video_bytes
        self._error = error
        self.calls: list[tuple[str, str]] = []

    async def swap_video(self, source_url: str, target_url: str) -> bytes:
        self.calls.append((source_url, target_url))
        if self._error is not None:
            raise GenerationError(self._error)
        assert self._video_bytes is not None
        return self._video_bytes


def make_clip_bytes(directory: Path) -> bytes:
    source = directory / "clip-src.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10:duration=1",
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(source)],
        check=True, capture_output=True,
    )
    return source.read_bytes()


async def _drain_queued_steps(session_maker: SessionMaker) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, 300)
            await session.commit()
        if claimed is None:
            return


async def make_target_video(
    http_client: AsyncClient, storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> str:
    upload = await create_ready_asset(http_client, storage)
    asset_id = uuid.UUID(upload["asset_id"])
    user_id = uuid.UUID(await current_user_id(http_client))
    async with session_maker() as session:
        asset = await session.get(Asset, asset_id)
        assert asset is not None
        asset.kind = "output_video"
        asset.content_type = "video/mp4"
        asset.byte_size = 100
        session.add(Job(user_id=user_id, kind="video", preset_slug="dolly-in",
                        input_asset_id=asset_id, idempotency_key=f"producer-{asset_id}",
                        status="succeeded", credit_cost=20,
                        output_video_asset_id=asset_id, duration_ms=TARGET_DURATION_MS))
        await session.commit()
    return str(upload["asset_id"])


async def _create_job(
    guest_client: AsyncClient, storage: InMemoryObjectStorage,
    session_maker: SessionMaker, key: str,
) -> uuid.UUID:
    source = await create_ready_asset(guest_client, storage)
    target = await make_target_video(guest_client, storage, session_maker)
    response = await guest_client.post(
        "/api/v1/video-faceswap-jobs",
        json={"source_asset_id": source["asset_id"], "target_asset_id": target,
              "idempotency_key": key},
    )
    assert response.status_code == 202
    return uuid.UUID(response.json()["id"])


async def _run_step(
    session_maker: SessionMaker, storage: InMemoryObjectStorage,
    adapter: object, job_id: uuid.UUID,
) -> None:
    claimed = await claim_step(session_maker, WORKER_ID, RUN_SETTINGS.lease_seconds)
    assert claimed is not None and claimed.job_id == job_id
    await run_claimed_step_for_kind(
        session_maker,
        storage=storage,  # type: ignore[arg-type]
        adapter=MockModelAdapter(Settings()),  # type: ignore[arg-type]
        image_adapter=PlaceholderImageAdapter("local-motion"),  # type: ignore[arg-type]
        video_face_swap_adapter=adapter,  # type: ignore[arg-type]
        claimed=claimed,
        worker_id=WORKER_ID,
        settings=RUN_SETTINGS,
    )


async def test_claimed_step_verifies_ffprobe_and_settles(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker, tmp_path: Path,
) -> None:
    await _drain_queued_steps(session_maker)
    job_id = await _create_job(guest_client, object_storage, session_maker, "t6b-step-ok-1")
    adapter = _FakeVideoFaceSwapAdapter(video_bytes=make_clip_bytes(tmp_path))

    await _run_step(session_maker, object_storage, adapter, job_id)

    body = (await guest_client.get(f"/api/v1/video-faceswap-jobs/{job_id}")).json()
    assert body["status"] == "succeeded"
    assert body["generated_by"] == "modal-video-faceswap"
    assert body["video_url"] is not None and body["poster_url"] is not None
    assert body["duration_ms"] == 1000
    assert len(adapter.calls) == 1
    assert await balance_of(guest_client) == GUEST_GRANT - TARGET_COST
    async with session_maker() as session:
        settled = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j AND kind = 'SETTLE'"),
            {"j": job_id},
        )
    assert settled == 1


async def test_faceless_video_fails_and_refunds_verbatim(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
) -> None:
    await _drain_queued_steps(session_maker)
    job_id = await _create_job(guest_client, object_storage, session_maker, "t6b-step-fail-1")
    adapter = _FakeVideoFaceSwapAdapter(error=NO_FACE_MESSAGE)

    await _run_step(session_maker, object_storage, adapter, job_id)

    body = (await guest_client.get(f"/api/v1/video-faceswap-jobs/{job_id}")).json()
    assert body["status"] == "failed"
    assert body["error_message"] == NO_FACE_MESSAGE
    assert body["video_url"] is None
    assert await balance_of(guest_client) == GUEST_GRANT
    async with session_maker() as session:
        released = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j AND kind = 'RELEASE'"),
            {"j": job_id},
        )
    assert released == 1


async def test_adapter_surfaces_422_detail_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = VideoFaceSwapAdapter(Settings(modal_video_faceswap_endpoint_url="https://x",
                                            modal_webhook_secret="s"))

    class _CannedClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "_CannedClient":
            return self

        async def __aexit__(self, *args: object) -> bool:
            return False

        async def post(self, *args: object, **kwargs: object) -> httpx.Response:
            return httpx.Response(422, json={"detail": NO_FACE_MESSAGE})

    monkeypatch.setattr(httpx, "AsyncClient", _CannedClient)
    try:
        await adapter.swap_video("memory://source", "memory://target")
    except GenerationError as error:
        assert error.user_message == NO_FACE_MESSAGE
    else:
        raise AssertionError("expected GenerationError")
