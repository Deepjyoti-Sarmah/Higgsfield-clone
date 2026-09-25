"""T-010-4: still→clip input, audio uploads, ledger read, Library and share extras."""

import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import (
    create_queued_job,
    create_ready_asset,
    current_user_id,
    post_job,
)
from tests.test_sequence_jobs_api import create_succeeded_clip

LIBRARY_URL = "/api/v1/jobs"
AUDIO_BYTES = b"ID3" + b"0" * 300


async def _create_audio_asset(
    client: AsyncClient, storage: InMemoryObjectStorage, extension: str = "mp3"
) -> dict[str, str]:
    created = await client.post(
        "/api/v1/uploads", json={"content_type": "audio/mpeg", "byte_size": len(AUDIO_BYTES)}
    )
    assert created.status_code == 201
    upload = created.json()
    key = f"users/{await current_user_id(client)}/inputs/{upload['asset_id']}.{extension}"
    storage.put_bytes(key, AUDIO_BYTES)
    completed = await client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")
    assert completed.status_code == 200
    return upload


async def _create_sequence(
    guest_client: AsyncClient, storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession], key: str,
) -> str:
    first = await create_succeeded_clip(guest_client, storage, session_maker, f"{key}-a")
    second = await create_succeeded_clip(guest_client, storage, session_maker, f"{key}-b")
    created = await guest_client.post("/api/v1/sequence-jobs", json={
        "clips": [{"job_id": first, "transition_in": "cut"},
                  {"job_id": second, "transition_in": "crossfade"}],
        "idempotency_key": key})
    assert created.status_code == 202
    return str(created.json()["id"])


async def test_own_output_image_seeds_a_clip(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)
    async with session_maker() as session:
        await session.execute(
            text("UPDATE asset SET kind = 'output_image' WHERE id = :id"),
            {"id": uuid.UUID(asset["asset_id"])})
        await session.commit()
    response = await post_job(guest_client, asset["asset_id"], "t0104-still-clip-1")
    assert response.status_code == 202


async def test_foreign_output_image_and_video_are_404(
    guest_client: AsyncClient, other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)
    async with session_maker() as session:
        await session.execute(
            text("UPDATE asset SET kind = 'output_image' WHERE id = :id"),
            {"id": uuid.UUID(asset["asset_id"])})
        await session.commit()
    foreign = await post_job(other_guest_client, asset["asset_id"], "t0104-still-clip-2")
    assert foreign.status_code == 404
    video_asset = await create_ready_asset(guest_client, object_storage)
    async with session_maker() as session:
        await session.execute(
            text("UPDATE asset SET kind = 'output_video' WHERE id = :id"),
            {"id": uuid.UUID(video_asset["asset_id"])})
        await session.commit()
    video = await post_job(guest_client, video_asset["asset_id"], "t0104-still-clip-3")
    assert video.status_code == 404


async def test_audio_upload_creates_pending_input_audio_mp3_key(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    created = await guest_client.post(
        "/api/v1/uploads", json={"content_type": "audio/mpeg", "byte_size": len(AUDIO_BYTES)}
    )
    assert created.status_code == 201
    upload = created.json()
    user_id = await current_user_id(guest_client)
    key = f"users/{user_id}/inputs/{upload['asset_id']}.mp3"
    assert key.endswith(".mp3")
    object_storage.put_bytes(key, AUDIO_BYTES)
    completed = await guest_client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")
    assert completed.status_code == 200
    async with session_maker() as session:
        row = await session.execute(
            text("SELECT kind, status FROM asset WHERE id = :id"),
            {"id": uuid.UUID(upload["asset_id"])})
        kind, status = row.first()
    assert (kind, status) == ("input_audio", "ready")


async def test_text_plain_upload_is_rejected(guest_client: AsyncClient) -> None:
    response = await guest_client.post(
        "/api/v1/uploads", json={"content_type": "text/plain", "byte_size": 10}
    )
    assert response.status_code == 422


async def test_ledger_lists_newest_first_and_only_own_rows(
    guest_client: AsyncClient, other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
) -> None:
    other_topup = await other_guest_client.post("/api/v1/credits/topup")
    assert other_topup.status_code == 200
    await guest_client.post("/api/v1/credits/topup")
    asset = await create_ready_asset(guest_client, object_storage)
    held = await post_job(guest_client, asset["asset_id"], "t0104-ledger-1")
    assert held.status_code == 202

    mine = await guest_client.get("/api/v1/credits/ledger?limit=10")
    theirs = await other_guest_client.get("/api/v1/credits/ledger?limit=10")

    assert mine.status_code == 200
    kinds = [entry["kind"] for entry in mine.json()["items"]]
    assert kinds == ["HOLD", "TOPUP", "GRANT"]
    assert all(entry["job_id"] is not None for entry in mine.json()["items"][:1])
    foreign_ids = {entry["id"] for entry in theirs.json()["items"]}
    assert foreign_ids.isdisjoint({entry["id"] for entry in mine.json()["items"]})


async def test_library_sequence_has_clip_count_and_image_has_images(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    assert (await guest_client.post("/api/v1/credits/topup")).status_code == 200
    sequence_id = await _create_sequence(
        guest_client, object_storage, session_maker, "t0104-library-seq")
    image_id = await create_queued_job(guest_client, object_storage, "t0104-library-img")

    items = {
        item["id"]: item
        for item in (await guest_client.get(LIBRARY_URL)).json()["items"]
    }

    assert items[sequence_id]["kind"] == "sequence"
    assert items[sequence_id]["clip_count"] == 2
    assert items[image_id]["kind"] == "video"
    assert items[image_id]["images"] == []


async def test_public_read_exposes_sequence_and_image_extras(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    assert (await guest_client.post("/api/v1/credits/topup")).status_code == 200
    sequence_id = await _create_sequence(
        guest_client, object_storage, session_maker, "t0104-share-seq")
    video_id = await create_queued_job(guest_client, object_storage, "t0104-share-vid")

    sequence = await guest_client.get(f"/api/v1/public/jobs/{sequence_id}")
    video = await guest_client.get(f"/api/v1/public/jobs/{video_id}")

    assert sequence.status_code == 200
    assert sequence.json()["kind"] == "sequence"
    assert sequence.json()["clip_count"] == 2
    assert sequence.json()["duration_ms"] is None
    assert sequence.json()["preset_slug"] is None
    assert video.status_code == 200
    assert video.json()["kind"] == "video"
    assert video.json()["clip_count"] is None
