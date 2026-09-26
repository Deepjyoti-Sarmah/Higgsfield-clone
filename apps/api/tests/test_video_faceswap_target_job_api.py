import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.video_faceswap_rules import video_faceswap_cost
from app.models.asset import Asset
from app.models.job import Job
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import (
    GUEST_GRANT,
    balance_of,
    create_queued_job,
    create_ready_asset,
    current_user_id,
)

SessionMaker = async_sessionmaker[AsyncSession]

TARGET_DURATION_MS = 5000
TARGET_COST = video_faceswap_cost(TARGET_DURATION_MS)


def _job_body(source: str, job_id: str, key: str) -> dict[str, object]:
    return {
        "source_asset_id": source,
        "target_job_id": job_id,
        "idempotency_key": key,
    }


async def make_target_video_job(
    http_client: AsyncClient,
    storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
    *,
    kind: str = "video",
) -> tuple[str, str]:
    upload = await create_ready_asset(http_client, storage)
    asset_id = uuid.UUID(upload["asset_id"])
    user_id = uuid.UUID(await current_user_id(http_client))
    async with session_maker() as session:
        asset = await session.get(Asset, asset_id)
        assert asset is not None
        asset.kind = "output_video"
        asset.content_type = "video/mp4"
        asset.byte_size = 100
        job = Job(user_id=user_id, kind=kind,
                  preset_slug="dolly-in" if kind == "video" else None,
                  input_asset_id=asset_id if kind == "video" else None,
                  idempotency_key=f"job-target-{asset_id}",
                  status="succeeded", credit_cost=20,
                  output_video_asset_id=asset_id, duration_ms=TARGET_DURATION_MS)
        session.add(job)
        await session.flush()
        job_id = job.id
        await session.commit()
    return str(upload["asset_id"]), str(job_id)


async def test_target_job_id_resolves_to_output_video(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source = await create_ready_asset(guest_client, object_storage)
    _, target_job = await make_target_video_job(guest_client, object_storage, session_maker)

    created = await guest_client.post("/api/v1/video-faceswap-jobs", json=_job_body(
        str(source["asset_id"]), target_job, "t6a-job-01"))

    assert created.status_code == 202
    body = created.json()
    assert (body["status"], body["credit_cost"]) == ("queued", TARGET_COST)
    assert await balance_of(guest_client) == GUEST_GRANT - TARGET_COST


async def test_target_job_id_accepts_sequence_jobs(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source = await create_ready_asset(guest_client, object_storage)
    _, target_job = await make_target_video_job(
        guest_client, object_storage, session_maker, kind="sequence")

    created = await guest_client.post("/api/v1/video-faceswap-jobs", json=_job_body(
        str(source["asset_id"]), target_job, "t6a-job-seq-01"))

    assert created.status_code == 202


async def test_foreign_target_job_is_404(
    guest_client: AsyncClient, other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    _, foreign_job = await make_target_video_job(
        other_guest_client, object_storage, session_maker)
    own = await create_ready_asset(guest_client, object_storage)

    created = await guest_client.post("/api/v1/video-faceswap-jobs", json=_job_body(
        str(own["asset_id"]), foreign_job, "t6a-job-404-01"))

    assert created.status_code == 404


async def test_target_job_without_video_is_422(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source = await create_ready_asset(guest_client, object_storage)
    queued_job = await create_queued_job(guest_client, object_storage, "t6a-job-novid-seed")

    created = await guest_client.post("/api/v1/video-faceswap-jobs", json=_job_body(
        str(source["asset_id"]), queued_job, "t6a-job-422-01"))

    assert created.status_code == 422
