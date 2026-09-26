import uuid

from httpx import AsyncClient
from sqlalchemy import text
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


def _body(source: str, target: str, key: str, keyframe: str | None = None) -> dict[str, object]:
    body: dict[str, object] = {
        "source_asset_id": source,
        "target_asset_id": target,
        "idempotency_key": key,
    }
    if keyframe is not None:
        body["keyframe_asset_id"] = keyframe
    return body


async def make_target_video(
    http_client: AsyncClient,
    storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
    *,
    duration_ms: int | None = TARGET_DURATION_MS,
    byte_size: int = 100,
    content_type: str = "video/mp4",
) -> str:
    upload = await create_ready_asset(http_client, storage)
    asset_id = uuid.UUID(upload["asset_id"])
    user_id = uuid.UUID(await current_user_id(http_client))
    async with session_maker() as session:
        asset = await session.get(Asset, asset_id)
        assert asset is not None
        asset.kind = "output_video"
        asset.content_type = content_type
        asset.byte_size = byte_size
        session.add(Job(user_id=user_id, kind="video", preset_slug="dolly-in",
                        input_asset_id=asset_id, idempotency_key=f"producer-{asset_id}",
                        status="succeeded", credit_cost=20,
                        output_video_asset_id=asset_id, duration_ms=duration_ms))
        await session.commit()
    return str(upload["asset_id"])


async def _source_and_target(
    guest_client: AsyncClient, storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> tuple[str, str]:
    source = await create_ready_asset(guest_client, storage)
    target = await make_target_video(guest_client, storage, session_maker)
    return str(source["asset_id"]), target


async def test_create_holds_per_second_cost(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source, target = await _source_and_target(guest_client, object_storage, session_maker)

    created = await guest_client.post(
        "/api/v1/video-faceswap-jobs", json=_body(source, target, "t6a-create-01"))

    assert created.status_code == 202
    body = created.json()
    assert (body["status"], body["credit_cost"]) == ("queued", TARGET_COST)
    assert await balance_of(guest_client) == GUEST_GRANT - TARGET_COST
    async with session_maker() as session:
        holds = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j AND kind = 'HOLD'"),
            {"j": uuid.UUID(body["id"])})
    assert holds == 1


async def test_keyframe_asset_id_is_accepted(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source, target = await _source_and_target(guest_client, object_storage, session_maker)
    keyframe = await create_ready_asset(guest_client, object_storage)

    created = await guest_client.post("/api/v1/video-faceswap-jobs", json=_body(
        source, target, "t6a-keyframe-01", str(keyframe["asset_id"])))

    assert created.status_code == 202


async def test_replay_returns_same_job_and_holds_once(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source, target = await _source_and_target(guest_client, object_storage, session_maker)
    body = _body(source, target, "t6a-idem-01")

    first = await guest_client.post("/api/v1/video-faceswap-jobs", json=body)
    second = await guest_client.post("/api/v1/video-faceswap-jobs", json=body)

    assert first.status_code == second.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert await balance_of(guest_client) == GUEST_GRANT - TARGET_COST


async def test_foreign_target_is_404(
    guest_client: AsyncClient, other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    foreign = await make_target_video(other_guest_client, object_storage, session_maker)
    own = await create_ready_asset(guest_client, object_storage)

    created = await guest_client.post("/api/v1/video-faceswap-jobs", json=_body(
        str(own["asset_id"]), foreign, "t6a-404-01"))

    assert created.status_code == 404


async def test_idempotency_key_cannot_cross_job_types(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    key = "t6a-cross-01"
    await create_queued_job(guest_client, object_storage, key)
    source, target = await _source_and_target(guest_client, object_storage, session_maker)

    response = await guest_client.post("/api/v1/video-faceswap-jobs", json=_body(source, target, key))

    assert response.status_code == 422


async def test_zero_balance_returns_402(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source, target = await _source_and_target(guest_client, object_storage, session_maker)
    for index in range(3):
        assert await create_queued_job(guest_client, object_storage, f"t6a-spend-{index}") is not None
    assert await balance_of(guest_client) == 0

    created = await guest_client.post(
        "/api/v1/video-faceswap-jobs", json=_body(source, target, "t6a-402-01"))

    assert created.status_code == 402
    assert created.json() == {"detail": "Not enough credits", "balance": 0, "required": TARGET_COST}


async def test_over_limit_targets_rejected_without_hold(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source = await create_ready_asset(guest_client, object_storage)
    too_long = await make_target_video(
        guest_client, object_storage, session_maker, duration_ms=31_000)
    too_big = await make_target_video(
        guest_client, object_storage, session_maker, byte_size=60_000_000)
    not_mp4 = await make_target_video(
        guest_client, object_storage, session_maker, content_type="video/webm")
    unknown = await make_target_video(
        guest_client, object_storage, session_maker, duration_ms=None)

    for index, target in enumerate([too_long, too_big, not_mp4, unknown]):
        response = await guest_client.post("/api/v1/video-faceswap-jobs", json=_body(
            str(source["asset_id"]), target, f"t6a-422-{index}"))
        assert response.status_code == 422

    assert await balance_of(guest_client) == GUEST_GRANT


async def test_read_own_and_not_others(
    guest_client: AsyncClient, other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage, session_maker: SessionMaker,
) -> None:
    source, target = await _source_and_target(guest_client, object_storage, session_maker)
    created = await guest_client.post(
        "/api/v1/video-faceswap-jobs", json=_body(source, target, "t6a-read-01"))
    job_id = created.json()["id"]

    owner = await guest_client.get(f"/api/v1/video-faceswap-jobs/{job_id}")
    stranger = await other_guest_client.get(f"/api/v1/video-faceswap-jobs/{job_id}")

    assert owner.status_code == 200
    body = owner.json()
    assert (body["status"], body["duration_ms"]) == ("queued", TARGET_DURATION_MS)
    assert body["source_url"] is not None and body["target_url"] is not None
    assert body["video_url"] is None and body["poster_url"] is None
    assert stranger.status_code == 404
