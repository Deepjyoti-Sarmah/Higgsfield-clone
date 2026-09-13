import asyncio
import base64
import subprocess
import uuid
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.modal_adapter import ModalAdapter
from app.adapters.model_adapter import (
    BackendNotConfiguredError,
    GenerationError,
    GenerationRequest,
    GenerationResult,
)
from app.repositories.job_steps import claim_next_queued_step
from app.repositories.jobs import find_job
from app.services import generation_runs
from app.services.generation_runs import RunSettings, run_claimed_step
from app.services.step_claiming import claim_step
from app.settings import Settings
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.fakes.scripted_model_adapter import VIDEO_SIZE, ScriptedModelAdapter
from tests.job_api_helpers import create_queued_job, current_user_id

WORKER_ID = "modal-worker"
DRAIN_WORKER = "modal-drain-worker"
LEASE_SECONDS = 1
SLOW_CALL_SECONDS = 0.7
ENDPOINT = "https://modal.example/clip"


def _request(work_dir: Path) -> GenerationRequest:
    image = "http://example.test/input.jpg"
    return GenerationRequest(uuid.uuid4(), "dolly-in", "slow dolly in",
                             work_dir / "input.jpg", image, work_dir)


def _settings(endpoint: str) -> Settings:
    return Settings(generation_backend="modal", modal_endpoint_url=endpoint,
                    modal_webhook_secret="wh-test")


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _client_class(seen: list[dict[str, Any]], response: Any = None, error: Any = None):
    class _FakeClient:
        def __init__(self, *a: Any, **k: Any) -> None:
            return None

        async def __aenter__(self) -> "_FakeClient":
            return self

        async def __aexit__(self, *a: Any) -> bool:
            return False

        async def post(self, url: str, json: Any = None, headers: Any = None) -> _FakeResponse:
            seen.append({"url": url, "json": json, "headers": headers})
            if error is not None:
                raise error
            return _FakeResponse(200, response)

    return _FakeClient


def _tiny_mp4(path: Path) -> bytes:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "testsrc=size=64x64:rate=1:duration=1",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path.read_bytes()


def _clip_payload(video: bytes) -> dict[str, Any]:
    return {"video_base64": base64.b64encode(video).decode("ascii"), "width": 960,
            "height": 544, "duration_ms": 5042}


async def _generate(work_dir: Path, endpoint: str = ENDPOINT) -> GenerationResult:
    return await ModalAdapter(_settings(endpoint)).generate_video(_request(work_dir))


async def test_missing_endpoint_is_not_configured(tmp_path: Path) -> None:
    adapter = ModalAdapter(Settings(generation_backend="modal"))
    with pytest.raises(BackendNotConfiguredError, match="not configured"):
        await adapter.generate_video(_request(tmp_path))


async def test_success_writes_video_and_poster(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    video = _tiny_mp4(tmp_path / "source.mp4")
    seen: list[dict[str, Any]] = []
    monkeypatch.setattr(httpx, "AsyncClient", _client_class(seen, _clip_payload(video)))
    result = await _generate(tmp_path)
    assert result.video_path.read_bytes() == video
    assert result.poster_path.read_bytes()[:2] == b"\xff\xd8"
    assert (result.width, result.height, result.duration_ms) == (960, 544, 5042)
    assert seen[0]["json"] == {"image_url": "http://example.test/input.jpg", "prompt": "slow dolly in"}
    assert seen[0]["headers"] == {"Authorization": "Bearer wh-test"}


@pytest.mark.parametrize("payload", [
    {"width": 960, "height": 544, "duration_ms": 5042},
    {"video_base64": "!!!", "width": 960, "height": 544, "duration_ms": 5042},
    {"video_base64": "", "width": 960, "height": 544, "duration_ms": 5042},
    {"video_base64": "eA==", "width": 0, "height": 544, "duration_ms": 5042},
    {"video_base64": "eA==", "width": 960, "height": -1, "duration_ms": 5042},
    ["not-a-dict"],
], ids=["missing-video", "bad-base64", "empty", "zero-width", "bad-height", "list-body"])
async def test_malformed_responses_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                        payload: Any) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", _client_class([], payload))
    with pytest.raises(GenerationError, match="refunded"):
        await _generate(tmp_path)


async def test_http_error_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[dict[str, Any]] = []

    class _ErrorClient(_client_class(seen)):
        async def post(self, url: str, json: Any = None, headers: Any = None) -> _FakeResponse:
            return _FakeResponse(500, {})

    monkeypatch.setattr(httpx, "AsyncClient", _ErrorClient)
    with pytest.raises(GenerationError, match="refunded"):
        await _generate(tmp_path)


async def test_timeout_reports_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", _client_class([], error=httpx.TimeoutException("t")))
    with pytest.raises(GenerationError, match="timed out"):
        await _generate(tmp_path)


class _SlowAdapter:
    name = "slow"

    def __init__(self, delay_seconds: float) -> None:
        self._delay_seconds = delay_seconds

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        await asyncio.sleep(self._delay_seconds)
        return ScriptedModelAdapter().write_tiny_outputs(request.work_dir)


async def _drain(session_maker: async_sessionmaker[AsyncSession]) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, LEASE_SECONDS)
            await session.commit()
        if claimed is None:
            return


async def test_slow_call_survives_lease_renewals(guest_client: Any,
                                                 object_storage: InMemoryObjectStorage,
                                                 session_maker: Any,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    await _drain(session_maker)
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "modal-lease-1"))
    user_id = await current_user_id(guest_client)
    claimed = await claim_step(session_maker, WORKER_ID, LEASE_SECONDS)
    assert claimed is not None and claimed.job_id == job_id
    renewals: list[uuid.UUID] = []
    real_renew = generation_runs.renew_step_lease

    async def _counting(session: Any, step_id: uuid.UUID, worker_id: str, lease: int) -> bool:
        renewals.append(step_id)
        return await real_renew(session, step_id, worker_id, lease)

    monkeypatch.setattr(generation_runs, "renew_step_lease", _counting)
    settings = RunSettings(lease_seconds=LEASE_SECONDS, generation_timeout_seconds=30,
                           download_url_ttl_seconds=3600)
    await run_claimed_step(session_maker, storage=object_storage,
                           adapter=_SlowAdapter(SLOW_CALL_SECONDS), claimed=claimed,
                           worker_id=WORKER_ID, settings=settings)
    assert len(renewals) >= 2
    async with session_maker() as session:
        job = await find_job(session, job_id)
        assert job is not None and job.status == "succeeded"
    video_key = f"users/{user_id}/jobs/{job_id}/video.mp4"
    assert await object_storage.read_object_size(video_key) == VIDEO_SIZE
