import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.mock_model_adapter import MockModelAdapter
from app.adapters.model_adapter import GenerationError
from app.adapters.placeholder_image_adapter import PlaceholderImageAdapter
from app.repositories.job_steps import claim_next_queued_step
from app.services.generation_runs import RunSettings
from app.services.step_claiming import claim_step
from app.settings import Settings
from app.worker import run_claimed_step_for_kind
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import GUEST_GRANT, balance_of, create_ready_asset

SessionMaker = async_sessionmaker[AsyncSession]
WORKER_ID = "faceswap-test-worker"
DRAIN_WORKER = "faceswap-drain-worker"
RUN_SETTINGS = RunSettings(
    lease_seconds=300, generation_timeout_seconds=30.0, download_url_ttl_seconds=900
)


class _FakeFaceSwapAdapter:
    def __init__(self, name: str, image_bytes: bytes | None = None, error: str | None = None):
        self.name = name
        self._image_bytes = image_bytes
        self._error = error
        self.calls: list[tuple[str, str]] = []

    async def swap(self, source_url: str, target_url: str) -> bytes:
        self.calls.append((source_url, target_url))
        if self._error is not None:
            raise GenerationError(self._error)
        assert self._image_bytes is not None
        return self._image_bytes


async def _drain_queued_steps(session_maker: SessionMaker) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, 300)
            await session.commit()
        if claimed is None:
            return


async def _create_faceswap_job(
    guest_client: AsyncClient, storage: InMemoryObjectStorage, key: str
) -> uuid.UUID:
    source = await create_ready_asset(guest_client, storage)
    target = await create_ready_asset(guest_client, storage)
    response = await guest_client.post(
        "/api/v1/faceswap-jobs",
        json={
            "source_asset_id": source["asset_id"],
            "target_asset_id": target["asset_id"],
            "idempotency_key": key,
        },
    )
    assert response.status_code == 202
    return uuid.UUID(response.json()["id"])


async def _run_step(
    session_maker: SessionMaker, storage: InMemoryObjectStorage, face_swap_adapter: object, job_id: uuid.UUID
) -> None:
    claimed = await claim_step(session_maker, WORKER_ID, RUN_SETTINGS.lease_seconds)
    assert claimed is not None and claimed.job_id == job_id
    await run_claimed_step_for_kind(
        session_maker,
        storage=storage,  # type: ignore[arg-type]
        adapter=MockModelAdapter(Settings()),  # type: ignore[arg-type]
        image_adapter=PlaceholderImageAdapter("local-motion"),  # type: ignore[arg-type]
        face_swap_adapter=face_swap_adapter,  # type: ignore[arg-type]
        claimed=claimed,
        worker_id=WORKER_ID,
        settings=RUN_SETTINGS,
    )


async def test_a_claimed_faceswap_step_stores_the_image_and_settles(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    await _drain_queued_steps(session_maker)
    job_id = await _create_faceswap_job(guest_client, object_storage, "t0114-step-ok-1")
    adapter = _FakeFaceSwapAdapter("modal-faceswap", image_bytes=b"\x89PNG-fake")

    await _run_step(session_maker, object_storage, adapter, job_id)

    body = (await guest_client.get(f"/api/v1/faceswap-jobs/{job_id}")).json()
    assert body["status"] == "succeeded"
    assert body["generated_by"] == "modal-faceswap"
    assert body["image_url"] is not None
    assert len(adapter.calls) == 1
    async with session_maker() as session:
        positions = list(
            (await session.execute(
                text("SELECT position FROM job_image WHERE job_id = :j"), {"j": job_id}
            )).scalars()
        )
        kinds = dict(
            (await session.execute(
                text("SELECT kind, count(*) FROM asset a JOIN job_image i ON i.asset_id = a.id "
                     "WHERE i.job_id = :j GROUP BY kind"), {"j": job_id}
            )).all()
        )
    assert positions == [0]
    assert kinds == {"output_image": 1}
    assert await balance_of(guest_client) == GUEST_GRANT - 8


async def test_no_face_found_fails_and_refunds_with_the_message(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    await _drain_queued_steps(session_maker)
    job_id = await _create_faceswap_job(guest_client, object_storage, "t0114-step-fail-1")
    adapter = _FakeFaceSwapAdapter("modal-faceswap", error="No face was found in the target image")

    await _run_step(session_maker, object_storage, adapter, job_id)

    body = (await guest_client.get(f"/api/v1/faceswap-jobs/{job_id}")).json()
    assert body["status"] == "failed"
    assert body["error_message"] == "No face was found in the target image"
    assert await balance_of(guest_client) == GUEST_GRANT
    async with session_maker() as session:
        released = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j AND kind = 'RELEASE'"),
            {"j": job_id},
        )
        images = await session.scalar(
            text("SELECT count(*) FROM job_image WHERE job_id = :j"), {"j": job_id}
        )
    assert (released, images) == (1, 0)
