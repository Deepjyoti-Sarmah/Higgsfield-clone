import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.job_views import read_owned_job
from app.settings import get_settings
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import (
    PRESET_NAME,
    create_pending_asset,
    create_queued_job,
    current_user_id,
)


async def insert_output_asset(
    session_maker: async_sessionmaker[AsyncSession],
    user_id: str,
    asset_id: uuid.UUID,
    *,
    kind: str,
    storage_key: str,
    content_type: str,
) -> None:
    statement = text(
        "INSERT INTO asset (id, user_id, kind, status, storage_key, content_type, byte_size)"
        " VALUES (:id, :user_id, :kind, 'ready', :storage_key, :content_type, 99)"
    )
    async with session_maker() as session:
        await session.execute(
            statement,
            {
                "id": asset_id,
                "user_id": uuid.UUID(user_id),
                "kind": kind,
                "storage_key": storage_key,
                "content_type": content_type,
            },
        )
        await session.commit()


async def insert_pending_input_job(
    session_maker: async_sessionmaker[AsyncSession], user_id: str, asset_id: str
) -> uuid.UUID:
    job_id = uuid.uuid4()
    statement = text(
        "INSERT INTO job (id, user_id, preset_slug, input_asset_id, idempotency_key,"
        " status, credit_cost) VALUES (:id, :user_id, 'dolly-in', :asset_id, :key, 'queued', 20)"
    )
    async with session_maker() as session:
        await session.execute(
            statement,
            {
                "id": job_id,
                "user_id": uuid.UUID(user_id),
                "asset_id": uuid.UUID(asset_id),
                "key": f"pending-{job_id}",
            },
        )
        await session.commit()
    return job_id


async def test_read_requires_a_cookie(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/jobs/{uuid.uuid4()}")

    assert response.status_code == 401


async def test_read_returns_the_job_with_an_input_url(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "read-own-key-01")

    response = await guest_client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == job_id
    assert body["status"] == "queued"
    assert body["preset_slug"] == "dolly-in"
    assert body["preset_name"] == PRESET_NAME
    assert body["prompt"] == "slow push in"
    assert body["credit_cost"] == 20
    assert body["input_image_url"].startswith("memory://")
    assert body["video_url"] is None
    assert body["poster_url"] is None
    assert body["error_message"] is None
    assert body["started_at"] is None
    assert body["finished_at"] is None


async def test_read_hides_the_url_of_a_pending_input(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_pending_asset(guest_client)
    user_id = await current_user_id(guest_client)
    job_id = await insert_pending_input_job(session_maker, user_id, asset["asset_id"])

    async with session_maker() as session:
        view = await read_owned_job(
            session, object_storage, get_settings(), uuid.UUID(user_id), job_id
        )

    assert view is not None
    assert view.input_image_url is None


async def test_read_exposes_output_urls_once_the_assets_are_ready(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(
        await create_queued_job(guest_client, object_storage, "read-output-key")
    )
    user_id = await current_user_id(guest_client)
    video_id, poster_id = uuid.uuid4(), uuid.uuid4()
    await insert_output_asset(
        session_maker,
        user_id,
        video_id,
        kind="output_video",
        storage_key=f"users/{user_id}/jobs/{job_id}/video.mp4",
        content_type="video/mp4",
    )
    await insert_output_asset(
        session_maker,
        user_id,
        poster_id,
        kind="output_poster",
        storage_key=f"users/{user_id}/jobs/{job_id}/poster.jpg",
        content_type="image/jpeg",
    )
    async with session_maker() as session:
        await session.execute(
            text(
                "UPDATE job SET status = 'succeeded', output_video_asset_id = :video_id,"
                " output_poster_asset_id = :poster_id WHERE id = :job_id"
            ),
            {"video_id": video_id, "poster_id": poster_id, "job_id": job_id},
        )
        await session.commit()

    response = await guest_client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["video_url"].endswith("video.mp4?get")
    assert body["poster_url"].endswith("poster.jpg?get")


async def test_reading_an_unknown_job_is_404(guest_client: AsyncClient) -> None:
    response = await guest_client.get(f"/api/v1/jobs/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_another_guest_cannot_read_the_job(
    guest_client: AsyncClient,
    other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "read-foreign-01")

    response = await other_guest_client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 404


async def test_another_guest_cannot_stream_the_events(
    guest_client: AsyncClient,
    other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "events-foreign-1")

    response = await other_guest_client.get(f"/api/v1/jobs/{job_id}/events")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
