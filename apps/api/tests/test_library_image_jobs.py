"""T-038: the Library became kind-agnostic, so image jobs must appear alongside video ones."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.mock_model_adapter import MockModelAdapter
from app.adapters.placeholder_image_adapter import PlaceholderImageAdapter
from app.repositories.job_steps import claim_next_queued_step
from app.services.generation_runs import RunSettings
from app.services.step_claiming import claim_step
from app.settings import Settings
from app.worker import run_claimed_step_for_kind
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import create_queued_job
from tests.test_library_api import LIBRARY_URL, item_map

SessionMaker = async_sessionmaker[AsyncSession]
IMAGE_STEP_WORKER = "library-image-test-worker"
IMAGE_DRAIN_WORKER = "library-image-drain-worker"
IMAGE_RUN_SETTINGS = RunSettings(
    lease_seconds=300, generation_timeout_seconds=30.0, download_url_ttl_seconds=900
)


async def _drain_queued_steps(session_maker: SessionMaker) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, IMAGE_DRAIN_WORKER, 300)
            await session.commit()
        if claimed is None:
            return


async def create_succeeded_image_job(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
    key: str,
) -> str:
    """Create + run an image job to completion so the Library sees real image_urls."""
    await _drain_queued_steps(session_maker)
    response = await guest_client.post(
        "/api/v1/image-jobs",
        json={
            "prompt": "a red bicycle",
            "aspect_ratio": "1:1",
            "quality": "standard",
            "count": 1,
            "idempotency_key": key,
        },
    )
    assert response.status_code == 202
    job_id = uuid.UUID(response.json()["id"])
    claimed = await claim_step(session_maker, IMAGE_STEP_WORKER, IMAGE_RUN_SETTINGS.lease_seconds)
    assert claimed is not None and claimed.job_id == job_id
    await run_claimed_step_for_kind(
        session_maker,
        storage=object_storage,  # type: ignore[arg-type]
        adapter=MockModelAdapter(Settings()),  # type: ignore[arg-type]
        image_adapter=PlaceholderImageAdapter("local-motion"),  # type: ignore[arg-type]
        claimed=claimed,
        worker_id=IMAGE_STEP_WORKER,
        settings=IMAGE_RUN_SETTINGS,
    )
    return str(job_id)


async def test_the_library_is_kind_agnostic_and_lists_image_jobs(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
) -> None:
    video_id = await create_queued_job(guest_client, object_storage, "library-mixed-video")
    image_id = await create_succeeded_image_job(
        guest_client, object_storage, session_maker, "library-mixed-image"
    )

    items = item_map((await guest_client.get(LIBRARY_URL)).json())

    assert set(items) == {video_id, image_id}
    assert items[video_id]["kind"] == "video"
    assert items[video_id]["preset_slug"] == "dolly-in"
    assert items[video_id]["image_urls"] == []
    assert items[image_id]["kind"] == "image"
    assert items[image_id]["status"] == "succeeded"
    assert items[image_id]["preset_slug"] is None
    assert items[image_id]["preset_name"] is None
    assert items[image_id]["prompt"] == "a red bicycle"
    assert items[image_id]["video_url"] is None
    assert len(items[image_id]["image_urls"]) == 1
    assert items[image_id]["thumbnail_url"] == items[image_id]["image_urls"][0]


async def test_image_jobs_sort_alongside_video_jobs_newest_first(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
) -> None:
    first = await create_queued_job(guest_client, object_storage, "library-order-mixed-1")
    second = await create_succeeded_image_job(
        guest_client, object_storage, session_maker, "library-order-mixed-2"
    )
    third = await create_queued_job(guest_client, object_storage, "library-order-mixed-3")

    ids = [item["id"] for item in (await guest_client.get(LIBRARY_URL)).json()["items"]]

    assert ids == [third, second, first]
