import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.mock_model_adapter import MockModelAdapter
from app.adapters.placeholder_image_adapter import PlaceholderImageAdapter
from app.domain.job_states import statuses_allowed_before
from app.models.asset import Asset
from app.models.job import Job
from app.repositories.job_steps import ClaimedStep, claim_next_queued_step
from app.repositories.jobs import notify_job_event, transition_job_status
from app.services.generation_runs import RunSettings
from app.settings import Settings
from app.worker import run_claimed_step_for_kind
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import balance_of, create_queued_job, current_user_id

SessionMaker = async_sessionmaker[AsyncSession]
WORKER_ID = "stitch-test-worker"
RUN_SETTINGS = RunSettings(
    lease_seconds=300, generation_timeout_seconds=60.0, download_url_ttl_seconds=900
)
SHORT_LEASE = RunSettings(
    lease_seconds=1, generation_timeout_seconds=60.0, download_url_ttl_seconds=900
)
RENDER_ERROR = "Render failed. Your credit was refunded."
MAKE_CLIP_ARGS = ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=960x544:rate=24:duration=2",
                  "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]


async def _claim_own_step(
    session_maker: SessionMaker, job_id: uuid.UUID, lease_seconds: int
) -> ClaimedStep:
    # Scoped to our job so parallel runs never steal (or feed) each other's steps.
    query = (
        "UPDATE job_step SET status = 'running', attempt = attempt + 1,"
        " lease_owner = :worker, lease_expires_at = now() + make_interval(secs => :lease),"
        " started_at = coalesce(started_at, now()), updated_at = now()"
        " WHERE id = (SELECT id FROM job_step WHERE job_id = :job"
        " AND status = 'queued' ORDER BY created_at LIMIT 1"
        " FOR UPDATE SKIP LOCKED)"
        " RETURNING id, job_id, kind, attempt"
    )
    async with session_maker() as session:
        row = (await session.execute(
            text(query), {"worker": WORKER_ID, "lease": lease_seconds, "job": job_id},
        )).first()
        assert row is not None
        await transition_job_status(
            session, row.job_id, "running", allowed_from=statuses_allowed_before("running"),
            started_at=datetime.now(UTC))
        await notify_job_event(session, row.job_id)
        await session.commit()
    return ClaimedStep(id=row.id, job_id=row.job_id, kind=row.kind, attempt=row.attempt)


def make_clip_bytes(directory: Path) -> bytes:
    source = directory / "clip-src.mp4"
    subprocess.run(MAKE_CLIP_ARGS + [str(source)], check=True, capture_output=True)
    return source.read_bytes()


async def _succeed_clip_with_bytes(
    session_maker: SessionMaker, storage: InMemoryObjectStorage,
    user_id: str, job_id: str, payload: bytes,
) -> None:
    key = f"users/{user_id}/jobs/{job_id}/video.mp4"
    storage.put_bytes(key, payload)
    async with session_maker() as session:
        session.add(Asset(id=uuid.uuid4(), user_id=uuid.UUID(user_id), kind="output_video",
                          status="ready", storage_key=key, content_type="video/mp4",
                          byte_size=len(payload)))
        job = await session.get(Job, uuid.UUID(job_id))
        assert job is not None
        job.status = "succeeded"
        asset_id = await session.scalar(
            text("SELECT id FROM asset WHERE storage_key = :key"), {"key": key})
        job.output_video_asset_id = asset_id
        assert asset_id is not None
        await session.commit()


async def _create_sequence(
    guest_client: AsyncClient, storage: InMemoryObjectStorage, session_maker: SessionMaker,
    key: str, payload: bytes,
) -> str:
    user_id = await current_user_id(guest_client)
    first = await create_queued_job(guest_client, storage, f"{key}-a")
    second = await create_queued_job(guest_client, storage, f"{key}-b")
    await _succeed_clip_with_bytes(session_maker, storage, user_id, first, payload)
    await _succeed_clip_with_bytes(session_maker, storage, user_id, second, payload)
    created = await guest_client.post("/api/v1/sequence-jobs", json={
        "clips": [{"job_id": first, "transition_in": "cut"},
                  {"job_id": second, "transition_in": "crossfade"}],
        "idempotency_key": key})
    assert created.status_code == 202
    return str(created.json()["id"])


async def _run_step(
    session_maker: SessionMaker, storage: InMemoryObjectStorage, job_id: uuid.UUID,
    settings: RunSettings = RUN_SETTINGS, lease_seconds: int = RUN_SETTINGS.lease_seconds,
) -> None:
    claimed = await _claim_own_step(session_maker, job_id, lease_seconds)
    await run_claimed_step_for_kind(
        session_maker, storage=storage, adapter=MockModelAdapter(Settings()),  # type: ignore[arg-type]
        image_adapter=PlaceholderImageAdapter("local-motion"),  # type: ignore[arg-type]
        claimed=claimed, worker_id=WORKER_ID, settings=settings)


async def _fetch_job(client: AsyncClient, job_id: uuid.UUID) -> dict:
    return (await client.get(f"/api/v1/sequence-jobs/{job_id}")).json()


async def test_stitch_step_succeeds_settles_and_records_duration(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker, tmp_path: Path,
) -> None:
    payload = make_clip_bytes(tmp_path)
    job_id = uuid.UUID(await _create_sequence(
        guest_client, object_storage, session_maker, "t0106-run-ok-1", payload))

    await _run_step(session_maker, object_storage, job_id)

    body = await _fetch_job(guest_client, job_id)
    assert (body["status"], body["generated_by"]) == ("succeeded", "ffmpeg")
    assert body["video_url"] is not None and body["poster_url"] is not None
    assert abs(body["duration_ms"] - 3500) < 500
    async with session_maker() as session:
        settled = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j AND kind = 'SETTLE'"),
            {"j": job_id})
        stored = await session.scalar(
            text("SELECT count(*) FROM asset WHERE storage_key LIKE :prefix"),
            {"prefix": f"%/jobs/{job_id}/%"})
    assert settled == 1 and stored == 2
    assert await balance_of(guest_client) == 19


async def _drain_queued_steps(session_maker: SessionMaker) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, "stitch-drain-worker", 300)
            await session.commit()
        if claimed is None:
            return


async def test_stitch_failure_fails_and_refunds(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker, tmp_path: Path,
) -> None:
    await _drain_queued_steps(session_maker)
    job_id = uuid.UUID(await _create_sequence(
        guest_client, object_storage, session_maker, "t0106-run-fail-1", b"not-a-video"))

    await _run_step(session_maker, object_storage, job_id)

    body = await _fetch_job(guest_client, job_id)
    assert (body["status"], body["error_message"]) == ("failed", RENDER_ERROR)
    async with session_maker() as session:
        released = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j AND kind = 'RELEASE'"),
            {"j": job_id})
    assert released == 1
    assert await balance_of(guest_client) == 20


async def test_lost_lease_writes_nothing(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker, tmp_path: Path,
) -> None:
    payload = make_clip_bytes(tmp_path)
    job_id = uuid.UUID(await _create_sequence(
        guest_client, object_storage, session_maker, "t0106-run-lost-1", payload))
    claimed = await _claim_own_step(session_maker, job_id, 1)
    steal = "UPDATE job_step SET lease_owner = 'thief' WHERE id = :s"
    async with session_maker() as session:
        await session.execute(text(steal), {"s": claimed.id})
        await session.commit()

    await run_claimed_step_for_kind(
        session_maker, storage=object_storage, adapter=MockModelAdapter(Settings()),  # type: ignore[arg-type]
        image_adapter=PlaceholderImageAdapter("local-motion"),  # type: ignore[arg-type]
        claimed=claimed, worker_id=WORKER_ID, settings=SHORT_LEASE)

    body = await _fetch_job(guest_client, job_id)
    assert body["status"] == "running"
    async with session_maker() as session:
        entries = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j"), {"j": job_id})
        outputs = await session.scalar(
            text("SELECT count(*) FROM asset WHERE storage_key LIKE :prefix"),
            {"prefix": f"%/jobs/{job_id}/%"})
    assert (entries, outputs) == (1, 0)
