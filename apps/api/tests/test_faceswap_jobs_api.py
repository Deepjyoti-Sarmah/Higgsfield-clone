import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.faceswap_rules import FACESWAP_CREDIT_COST
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import GUEST_GRANT, balance_of, create_queued_job, create_ready_asset

SessionMaker = async_sessionmaker[AsyncSession]


def _body(source_id: str, target_id: str, key: str) -> dict[str, object]:
    return {"source_asset_id": source_id, "target_asset_id": target_id, "idempotency_key": key}


async def _two_ready_assets(
    guest_client: AsyncClient, storage: InMemoryObjectStorage
) -> tuple[str, str]:
    source = await create_ready_asset(guest_client, storage)
    target = await create_ready_asset(guest_client, storage)
    return source["asset_id"], target["asset_id"]


async def test_create_holds_the_credit_cost(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source, target = await _two_ready_assets(guest_client, object_storage)

    created = await guest_client.post(
        "/api/v1/faceswap-jobs", json=_body(source, target, "t0114-create-01")
    )

    assert created.status_code == 202
    body = created.json()
    assert (body["status"], body["credit_cost"]) == ("queued", FACESWAP_CREDIT_COST)
    assert await balance_of(guest_client) == GUEST_GRANT - FACESWAP_CREDIT_COST
    async with session_maker() as session:
        holds = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j AND kind = 'HOLD'"),
            {"j": uuid.UUID(body["id"])},
        )
    assert holds == 1


async def test_the_same_key_returns_the_same_job_and_holds_once(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    source, target = await _two_ready_assets(guest_client, object_storage)
    body = _body(source, target, "t0114-idem-01")

    first = await guest_client.post("/api/v1/faceswap-jobs", json=body)
    second = await guest_client.post("/api/v1/faceswap-jobs", json=body)

    assert first.status_code == second.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert await balance_of(guest_client) == GUEST_GRANT - FACESWAP_CREDIT_COST


async def test_a_foreign_asset_is_404(
    guest_client: AsyncClient,
    other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
) -> None:
    foreign = await create_ready_asset(other_guest_client, object_storage)
    own = await create_ready_asset(guest_client, object_storage)

    created = await guest_client.post(
        "/api/v1/faceswap-jobs", json=_body(foreign["asset_id"], own["asset_id"], "t0114-404-01")
    )

    assert created.status_code == 404


async def test_an_idempotency_key_cannot_cross_job_types(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    key = "t0114-cross-01"
    await create_queued_job(guest_client, object_storage, key)
    source, target = await _two_ready_assets(guest_client, object_storage)

    response = await guest_client.post("/api/v1/faceswap-jobs", json=_body(source, target, key))

    assert response.status_code == 422


async def test_zero_balance_returns_402(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    source, target = await _two_ready_assets(guest_client, object_storage)
    for index in range(3):
        spend = await create_queued_job(guest_client, object_storage, f"t0114-spend-{index}")
        assert spend is not None
    assert await balance_of(guest_client) == 0

    created = await guest_client.post(
        "/api/v1/faceswap-jobs", json=_body(source, target, "t0114-402-01")
    )

    assert created.status_code == 402
    assert created.json() == {
        "detail": "Not enough credits", "balance": 0, "required": FACESWAP_CREDIT_COST
    }


async def test_daily_cap_returns_429(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    await guest_client.post("/api/v1/credits/topup")
    await guest_client.post("/api/v1/credits/topup")
    for index in range(10):
        assert await create_queued_job(guest_client, object_storage, f"t0114-cap-{index}") is not None
    source, target = await _two_ready_assets(guest_client, object_storage)

    created = await guest_client.post(
        "/api/v1/faceswap-jobs", json=_body(source, target, "t0114-429-01")
    )

    assert created.status_code == 429


async def test_read_own_and_not_others(
    guest_client: AsyncClient,
    other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
) -> None:
    source, target = await _two_ready_assets(guest_client, object_storage)
    created = await guest_client.post(
        "/api/v1/faceswap-jobs", json=_body(source, target, "t0114-read-01")
    )
    job_id = created.json()["id"]

    owner = await guest_client.get(f"/api/v1/faceswap-jobs/{job_id}")
    stranger = await other_guest_client.get(f"/api/v1/faceswap-jobs/{job_id}")

    assert owner.status_code == 200
    body = owner.json()
    assert body["status"] == "queued"
    assert body["source_url"] is not None and body["target_url"] is not None
    assert body["image_url"] is None
    assert stranger.status_code == 404
