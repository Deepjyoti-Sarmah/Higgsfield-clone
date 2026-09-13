import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import PRESET_NAME, create_queued_job, current_user_id

LIBRARY_URL = "/api/v1/jobs"


async def insert_asset(
    session_maker: async_sessionmaker[AsyncSession], user_id: str, kind: str, *, status: str = "ready"
) -> uuid.UUID:
    asset_id = uuid.uuid4()
    content_type = "video/mp4" if kind == "output_video" else "image/jpeg"
    async with session_maker() as session:
        await session.execute(
            text(
                "INSERT INTO asset (id, user_id, kind, status, storage_key, content_type, byte_size)"
                " VALUES (:id, :user_id, :kind, :status, :key, :content_type, 10)"
            ),
            {
                "id": asset_id, "user_id": uuid.UUID(user_id), "kind": kind, "status": status,
                "key": f"users/{user_id}/library/{asset_id}", "content_type": content_type,
            },
        )
        await session.commit()
    return asset_id


async def update_job(
    session_maker: async_sessionmaker[AsyncSession],
    job_id: str,
    *,
    status: str,
    video_id: uuid.UUID | None = None,
    poster_id: uuid.UUID | None = None,
    error_message: str | None = None,
) -> None:
    async with session_maker() as session:
        await session.execute(
            text(
                "UPDATE job SET status = :status, output_video_asset_id = :video,"
                " output_poster_asset_id = :poster, error_message = :error WHERE id = :job_id"
            ),
            {
                "status": status, "video": video_id, "poster": poster_id,
                "error": error_message, "job_id": uuid.UUID(job_id),
            },
        )
        await session.commit()


async def insert_job_with_pending_input(
    session_maker: async_sessionmaker[AsyncSession], user_id: str
) -> str:
    asset_id = await insert_asset(session_maker, user_id, "input_image", status="pending")
    job_id = uuid.uuid4()
    async with session_maker() as session:
        await session.execute(
            text(
                "INSERT INTO job (id, user_id, preset_slug, input_asset_id, idempotency_key,"
                " status, credit_cost) VALUES (:id, :user_id, 'dolly-in', :input, :key, 'queued', 20)"
            ),
            {"id": job_id, "user_id": uuid.UUID(user_id), "input": asset_id, "key": f"lib-{job_id}"},
        )
        await session.commit()
    return str(job_id)


def item_map(body: dict) -> dict[str, dict]:
    return {item["id"]: item for item in body["items"]}


async def test_list_requires_a_cookie(client: AsyncClient) -> None:
    response = await client.get(LIBRARY_URL)

    assert response.status_code == 401


async def test_list_is_newest_first_with_the_item_shape(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    empty = await guest_client.get(LIBRARY_URL)
    assert (empty.status_code, empty.json()) == (200, {"items": []})
    created = [
        await create_queued_job(guest_client, object_storage, f"library-order-{index}")
        for index in range(3)
    ]

    response = await guest_client.get(LIBRARY_URL)

    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["id"] for item in items} == set(created)
    times = [item["created_at"] for item in items]
    assert times == sorted(times, reverse=True)
    assert all(item["preset_name"] == PRESET_NAME for item in items)
    assert all(item["video_url"] is None for item in items)


async def test_limit_truncates_to_the_newest_and_rejects_out_of_bounds(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    for index in range(2):
        await create_queued_job(guest_client, object_storage, f"library-limit-{index}")

    everything = (await guest_client.get(LIBRARY_URL)).json()["items"]
    one = await guest_client.get(LIBRARY_URL, params={"limit": 1})
    too_small = await guest_client.get(LIBRARY_URL, params={"limit": 0})
    too_large = await guest_client.get(LIBRARY_URL, params={"limit": 101})

    assert one.status_code == 200
    assert one.json()["items"] == everything[:1]
    assert (too_small.status_code, too_large.status_code) == (422, 422)


async def test_another_guest_never_sees_foreign_jobs(
    guest_client: AsyncClient,
    other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
) -> None:
    mine = await create_queued_job(guest_client, object_storage, "library-owner-mine")
    theirs = await create_queued_job(other_guest_client, object_storage, "library-owner-theirs")

    my_items = (await guest_client.get(LIBRARY_URL)).json()["items"]
    their_items = (await other_guest_client.get(LIBRARY_URL)).json()["items"]

    assert [item["id"] for item in my_items] == [mine]
    assert [item["id"] for item in their_items] == [theirs]


async def test_thumbnail_prefers_the_ready_poster_then_input_then_none(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await current_user_id(guest_client)
    with_poster = await create_queued_job(guest_client, object_storage, "library-thumb-poster")
    video_id = await insert_asset(session_maker, user_id, "output_video")
    poster_id = await insert_asset(session_maker, user_id, "output_poster")
    await update_job(
        session_maker, with_poster, status="succeeded", video_id=video_id, poster_id=poster_id
    )
    input_only = await create_queued_job(guest_client, object_storage, "library-thumb-input")
    pending_poster = await insert_asset(session_maker, user_id, "output_poster", status="pending")
    await update_job(session_maker, input_only, status="succeeded", poster_id=pending_poster)
    no_asset = await insert_job_with_pending_input(session_maker, user_id)

    items = item_map((await guest_client.get(LIBRARY_URL)).json())
    poster_detail = (await guest_client.get(f"{LIBRARY_URL}/{with_poster}")).json()
    input_detail = (await guest_client.get(f"{LIBRARY_URL}/{input_only}")).json()

    assert items[with_poster]["thumbnail_url"] == poster_detail["poster_url"]
    assert items[with_poster]["video_url"] == poster_detail["video_url"]
    assert items[input_only]["thumbnail_url"] == input_detail["input_image_url"]
    assert input_detail["poster_url"] is None
    assert items[no_asset]["thumbnail_url"] is None


async def test_failed_carries_its_error_and_queued_has_no_video(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    failed = await create_queued_job(guest_client, object_storage, "library-failed")
    await update_job(session_maker, failed, status="failed", error_message="Model exploded")
    queued = await create_queued_job(guest_client, object_storage, "library-queued")

    items = item_map((await guest_client.get(LIBRARY_URL)).json())

    assert items[failed]["status"] == "failed"
    assert items[failed]["error_message"] == "Model exploded"
    assert items[failed]["video_url"] is None
    assert items[queued]["status"] == "queued"
    assert items[queued]["error_message"] is None
    assert items[queued]["video_url"] is None


async def test_preset_name_falls_back_to_the_slug_when_the_preset_is_inactive(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await create_queued_job(guest_client, object_storage, "library-inactive-preset")
    async with session_maker() as session:
        await session.execute(text("UPDATE preset SET is_active = false WHERE slug = 'dolly-in'"))
        await session.commit()
    try:
        items = (await guest_client.get(LIBRARY_URL)).json()["items"]
        assert [(item["preset_slug"], item["preset_name"]) for item in items] == [
            ("dolly-in", "dolly-in")
        ]
    finally:
        async with session_maker() as session:
            await session.execute(text("UPDATE preset SET is_active = true WHERE slug = 'dolly-in'"))
            await session.commit()
