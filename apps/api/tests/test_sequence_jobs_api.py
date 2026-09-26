import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.sequence_rules import MAX_CLIPS, MIN_CLIPS
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import (
    balance_of,
    create_queued_job,
    create_ready_asset,
    current_user_id,
    post_job,
)
from tests.sequence_helpers import (
    build_sequence_body,
    clip_rows,
    count_where,
    create_succeeded_clip,
    create_succeeded_video_faceswap,
)

SessionMaker = async_sessionmaker[AsyncSession]


async def test_create_writes_hold_step_and_clips(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    first = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-aa")
    second = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-bb")
    created = await guest_client.post(
        "/api/v1/sequence-jobs", json=build_sequence_body([first, second], "t0103-seq-01"))
    assert created.status_code == 202
    body = created.json()
    assert (body["status"], body["credit_cost"], body["clip_count"]) == ("queued", 1, 2)
    job_id = uuid.UUID(body["id"])
    assert await count_where(
        session_maker, "ledger_entry", "job_id = :job_id AND kind = 'HOLD'", job_id) == 1
    assert await count_where(
        session_maker, "job_step", "job_id = :job_id AND kind = 'stitch_video'", job_id) == 1
    assert await clip_rows(session_maker, job_id) == [(0, "cut"), (1, "crossfade")]
    assert await balance_of(guest_client) == 60 - 2 * 20 - 1


async def test_same_key_returns_same_job_and_holds_once(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    first = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-cc")
    second = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-dd")
    body = build_sequence_body([first, second], "t0103-seq-02")
    first_post = await guest_client.post("/api/v1/sequence-jobs", json=body)
    second_post = await guest_client.post("/api/v1/sequence-jobs", json=body)
    assert first_post.status_code == second_post.status_code == 202
    assert first_post.json()["id"] == second_post.json()["id"]
    job_id = uuid.UUID(first_post.json()["id"])
    assert await count_where(session_maker, "ledger_entry", "job_id = :job_id AND kind = 'HOLD'", job_id) == 1


async def test_key_of_image_job_conflicts(guest_client: AsyncClient) -> None:
    image = await guest_client.post("/api/v1/image-jobs", json={
        "prompt": "x", "aspect_ratio": "16:9", "quality": "standard", "count": 1,
        "idempotency_key": "t0103-seq-03"})
    assert image.status_code == 202
    created = await guest_client.post("/api/v1/sequence-jobs", json={
        "clips": [{"job_id": str(uuid.uuid4()), "transition_in": "cut"} for _ in range(MIN_CLIPS)],
        "idempotency_key": "t0103-seq-03"})
    assert created.status_code == 422


async def test_foreign_clip_is_404(
    guest_client: AsyncClient, other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    foreign = await create_succeeded_clip(other_guest_client, object_storage, session_maker, "t0103-ee")
    own = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-ff")
    created = await guest_client.post(
        "/api/v1/sequence-jobs", json=build_sequence_body([own, foreign], "t0103-seq-04"))
    assert created.status_code == 404


async def test_queued_or_image_clip_is_422(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    queued = await create_queued_job(guest_client, object_storage, "t0103-gg")
    good = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-hh")
    image = await guest_client.post("/api/v1/image-jobs", json={
        "prompt": "x", "aspect_ratio": "16:9", "quality": "standard", "count": 1,
        "idempotency_key": "t0103-seq-05-img"})
    assert image.status_code == 202
    queued_post = await guest_client.post(
        "/api/v1/sequence-jobs", json=build_sequence_body([good, queued], "t0103-seq-05"))
    image_post = await guest_client.post(
        "/api/v1/sequence-jobs", json=build_sequence_body([good, image.json()["id"]], "t0103-seq-06"))
    assert queued_post.status_code == 422
    assert image_post.status_code == 422


async def test_face_swapped_video_can_join_a_sequence(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    first = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-sw-a")
    swapped = await create_succeeded_video_faceswap(guest_client, session_maker, "t0103-sw-b")
    created = await guest_client.post(
        "/api/v1/sequence-jobs", json=build_sequence_body([first, swapped], "t0103-seq-swap"))
    assert created.status_code == 202
    assert created.json()["clip_count"] == 2


async def test_non_audio_asset_is_404(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    first = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-ii")
    second = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-jj")
    picture = await create_ready_asset(guest_client, object_storage)
    created = await guest_client.post(
        "/api/v1/sequence-jobs",
        json=build_sequence_body([first, second], "t0103-seq-07", picture["asset_id"]))
    assert created.status_code == 404


async def test_zero_balance_returns_402_without_a_job_row(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
) -> None:
    first = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-mm")
    second = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-nn")
    asset = await create_ready_asset(guest_client, object_storage)
    assert (await post_job(guest_client, asset["asset_id"], "t0103-spend-00")).status_code == 202
    assert await balance_of(guest_client) == 0
    created = await guest_client.post(
        "/api/v1/sequence-jobs", json=build_sequence_body([first, second], "t0103-seq-08"))
    assert created.status_code == 402
    assert created.json()["balance"] == 0 and created.json()["required"] == 1
    items = (await guest_client.get("/api/v1/jobs")).json()["items"]
    assert all(item["kind"] != "sequence" for item in items)


async def test_daily_cap_returns_429(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage,
) -> None:
    await guest_client.post("/api/v1/credits/topup")
    await guest_client.post("/api/v1/credits/topup")
    for index in range(10):
        assert await create_queued_job(guest_client, object_storage, f"t0103-cap-{index}") is not None
    created = await guest_client.post("/api/v1/sequence-jobs", json=build_sequence_body(
        [str(uuid.uuid4()) for _ in range(MAX_CLIPS)], "t0103-seq-09"))
    assert created.status_code == 429


async def test_read_own_and_not_others(
    guest_client: AsyncClient, other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    user_id = await current_user_id(guest_client)
    first = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-kk")
    second = await create_succeeded_clip(guest_client, object_storage, session_maker, "t0103-ll")
    created = await guest_client.post(
        "/api/v1/sequence-jobs", json=build_sequence_body([first, second], "t0103-seq-10"))
    assert created.status_code == 202
    read = await guest_client.get(f"/api/v1/sequence-jobs/{created.json()['id']}")
    foreign = await other_guest_client.get(f"/api/v1/sequence-jobs/{created.json()['id']}")
    assert read.status_code == 200
    body = read.json()
    assert [clip["job_id"] for clip in body["clips"]] == [first, second]
    assert body["clips"][0]["thumbnail_url"] == f"memory://users/{user_id}/jobs/{first}/poster.jpg?get"
    assert body["video_url"] is None and body["has_audio"] is False
    assert foreign.status_code == 404
