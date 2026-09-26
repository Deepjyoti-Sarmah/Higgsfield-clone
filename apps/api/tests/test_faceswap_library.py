import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.job_steps import claim_next_queued_step
from app.services.generation_runs import RunSettings
from app.services.step_claiming import claim_step
from app.worker import run_claimed_step_for_kind
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import create_ready_asset
from tests.test_faceswap_step import _FakeFaceSwapAdapter
from tests.test_library_api import LIBRARY_URL, item_map

SessionMaker = async_sessionmaker[AsyncSession]
LIBRARY_WORKER = "library-faceswap-test-worker"
LIBRARY_DRAIN_WORKER = "library-faceswap-drain-worker"
LIBRARY_RUN_SETTINGS = RunSettings(
    lease_seconds=300, generation_timeout_seconds=30.0, download_url_ttl_seconds=900
)


async def _drain_queued_steps(session_maker: SessionMaker) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, LIBRARY_DRAIN_WORKER, 300)
            await session.commit()
        if claimed is None:
            return


async def _create_succeeded_faceswap_job(
    guest_client: AsyncClient, storage: InMemoryObjectStorage, session_maker: SessionMaker, key: str
) -> str:
    await _drain_queued_steps(session_maker)
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
    job_id = uuid.UUID(response.json()["id"])
    claimed = await claim_step(session_maker, LIBRARY_WORKER, LIBRARY_RUN_SETTINGS.lease_seconds)
    assert claimed is not None and claimed.job_id == job_id
    adapter = _FakeFaceSwapAdapter("modal-faceswap", image_bytes=b"\x89PNG-fake")
    await run_claimed_step_for_kind(
        session_maker,
        storage=storage,  # type: ignore[arg-type]
        adapter=None,  # type: ignore[arg-type]
        image_adapter=None,  # type: ignore[arg-type]
        face_swap_adapter=adapter,  # type: ignore[arg-type]
        claimed=claimed,
        worker_id=LIBRARY_WORKER,
        settings=LIBRARY_RUN_SETTINGS,
    )
    return str(job_id)


async def test_the_library_shows_images_for_a_faceswap_job(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    job_id = await _create_succeeded_faceswap_job(
        guest_client, object_storage, session_maker, "t0114-lib-01"
    )

    items = item_map((await guest_client.get(LIBRARY_URL)).json())

    assert items[job_id]["kind"] == "faceswap"
    assert items[job_id]["status"] == "succeeded"
    assert len(items[job_id]["image_urls"]) == 1
    assert items[job_id]["thumbnail_url"] == items[job_id]["image_urls"][0]
    assert [image["url"] for image in items[job_id]["images"]] == items[job_id]["image_urls"]
