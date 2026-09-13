import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import PRESET_NAME, create_queued_job, current_user_id

PUBLIC_KEYS = {
    "id",
    "status",
    "preset_slug",
    "preset_name",
    "poster_url",
    "video_url",
    "created_at",
}
PRIVATE_FAILURE_TEXT = "private provider failure text"


async def _insert_ready_asset(
    session_maker: async_sessionmaker[AsyncSession],
    user_id: str,
    asset_id: uuid.UUID,
    *,
    kind: str,
    storage_key: str,
    content_type: str,
) -> None:
    async with session_maker() as session:
        await session.execute(
            text(
                "INSERT INTO asset (id, user_id, kind, status, storage_key, content_type, byte_size)"
                " VALUES (:id, :user_id, :kind, 'ready', :storage_key, :content_type, 99)"
            ),
            {
                "id": asset_id,
                "user_id": uuid.UUID(user_id),
                "kind": kind,
                "storage_key": storage_key,
                "content_type": content_type,
            },
        )
        await session.commit()


async def _update_job(
    session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID, **columns: object
) -> None:
    assignments = ", ".join(f"{name} = :{name}" for name in columns)
    async with session_maker() as session:
        await session.execute(
            text(f"UPDATE job SET {assignments} WHERE id = :job_id"),
            {**columns, "job_id": job_id},
        )
        await session.commit()


async def _set_preset_active(
    session_maker: async_sessionmaker[AsyncSession], slug: str, is_active: bool
) -> None:
    async with session_maker() as session:
        await session.execute(
            text("UPDATE preset SET is_active = :is_active WHERE slug = :slug"),
            {"is_active": is_active, "slug": slug},
        )
        await session.commit()


async def test_public_read_needs_no_cookie(
    client: AsyncClient, guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "share-anon-01")

    response = await client.get(f"/api/v1/public/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PUBLIC_KEYS
    assert body["id"] == job_id
    assert body["status"] == "queued"
    assert body["preset_slug"] == "dolly-in"
    assert body["preset_name"] == PRESET_NAME
    assert body["poster_url"] is None
    assert body["video_url"] is None


async def test_public_read_unknown_id_is_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/public/jobs/{uuid.uuid4()}")

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


async def test_public_read_rejects_a_malformed_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/public/jobs/not-a-uuid")

    assert response.status_code == 422


async def test_succeeded_job_exposes_ready_output_urls(
    client: AsyncClient,
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "share-done-01"))
    user_id = await current_user_id(guest_client)
    video_id, poster_id = uuid.uuid4(), uuid.uuid4()
    await _insert_ready_asset(
        session_maker,
        user_id,
        video_id,
        kind="output_video",
        storage_key=f"users/{user_id}/jobs/{job_id}/video.mp4",
        content_type="video/mp4",
    )
    await _insert_ready_asset(
        session_maker,
        user_id,
        poster_id,
        kind="output_poster",
        storage_key=f"users/{user_id}/jobs/{job_id}/poster.jpg",
        content_type="image/jpeg",
    )
    await _update_job(
        session_maker,
        job_id,
        status="succeeded",
        output_video_asset_id=video_id,
        output_poster_asset_id=poster_id,
    )

    response = await client.get(f"/api/v1/public/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PUBLIC_KEYS
    assert body["status"] == "succeeded"
    assert body["video_url"].endswith("video.mp4?get")
    assert body["poster_url"].endswith("poster.jpg?get")


async def test_failed_job_hides_the_error_message(
    client: AsyncClient,
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "share-fail-01"))
    await _update_job(session_maker, job_id, status="failed", error_message=PRIVATE_FAILURE_TEXT)

    response = await client.get(f"/api/v1/public/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PUBLIC_KEYS
    assert body["status"] == "failed"
    assert body["video_url"] is None
    assert body["poster_url"] is None
    assert "error_message" not in body
    assert "prompt" not in body
    assert PRIVATE_FAILURE_TEXT not in response.text


async def test_preset_name_falls_back_to_the_slug_when_inactive(
    client: AsyncClient,
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "share-inactive-1")
    await _set_preset_active(session_maker, "dolly-in", False)
    try:
        response = await client.get(f"/api/v1/public/jobs/{job_id}")
    finally:
        await _set_preset_active(session_maker, "dolly-in", True)

    assert response.status_code == 200
    assert response.json()["preset_name"] == "dolly-in"


async def test_every_visitor_gets_the_same_public_bytes(
    client: AsyncClient,
    guest_client: AsyncClient,
    other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "share-public-02")
    owner_id = await current_user_id(guest_client)

    anonymous = await client.get(f"/api/v1/public/jobs/{job_id}")
    stranger = await other_guest_client.get(f"/api/v1/public/jobs/{job_id}")
    owner = await guest_client.get(f"/api/v1/public/jobs/{job_id}")

    assert anonymous.status_code == stranger.status_code == owner.status_code == 200
    assert anonymous.json() == stranger.json() == owner.json()
    assert set(anonymous.json()) == PUBLIC_KEYS
    assert owner_id not in anonymous.text
