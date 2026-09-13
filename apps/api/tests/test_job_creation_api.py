import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import (
    GUEST_GRANT,
    PRESET_COST,
    balance_of,
    count_job_rows,
    create_pending_asset,
    create_ready_asset,
    current_user_id,
    post_job,
)


async def test_create_returns_202_and_writes_job_step_and_hold(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)

    response = await post_job(guest_client, asset["asset_id"], "create-key-0001")

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["credit_cost"] == PRESET_COST
    job_id = uuid.UUID(body["id"])
    assert await count_job_rows(session_maker, "job", job_id) == 1
    assert await count_job_rows(session_maker, "job_step", job_id) == 1
    assert await count_job_rows(session_maker, "ledger_entry", job_id) == 1
    assert await balance_of(guest_client) == GUEST_GRANT - PRESET_COST


async def test_created_rows_are_queued_and_the_hold_is_negative(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)
    created = await post_job(guest_client, asset["asset_id"], "create-key-0002")
    job_id = uuid.UUID(created.json()["id"])

    async with session_maker() as session:
        step_status = await session.scalar(
            text("SELECT status FROM job_step WHERE job_id = :job_id"), {"job_id": job_id}
        )
        kind, amount = (
            await session.execute(
                text("SELECT kind, amount FROM ledger_entry WHERE job_id = :job_id"),
                {"job_id": job_id},
            )
        ).one()
        input_asset_id = await session.scalar(
            text("SELECT input_asset_id FROM job WHERE id = :job_id"), {"job_id": job_id}
        )
        prompt = await session.scalar(
            text("SELECT prompt FROM job WHERE id = :job_id"), {"job_id": job_id}
        )

    assert step_status == "queued"
    assert (kind, amount) == ("HOLD", -PRESET_COST)
    assert str(input_asset_id) == asset["asset_id"]
    assert prompt == "slow push in"


async def test_insufficient_credits_is_a_top_level_402(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)
    for index in range(3):
        key = f"spend-key-{index:04d}"
        assert (await post_job(guest_client, asset["asset_id"], key)).status_code == 202
    assert await balance_of(guest_client) == 0

    response = await post_job(guest_client, asset["asset_id"], "spend-key-9999")

    assert response.status_code == 402
    assert response.json() == {"detail": "Not enough credits", "balance": 0, "required": PRESET_COST}
    user_id = uuid.UUID(await current_user_id(guest_client))
    async with session_maker() as session:
        jobs = await session.scalar(
            text("SELECT count(*) FROM job WHERE user_id = :user_id"), {"user_id": user_id}
        )
    assert jobs == 3


async def test_unknown_preset_is_404(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)

    response = await post_job(guest_client, asset["asset_id"], "unknown-preset-1", slug="nope")

    assert response.status_code == 404


async def test_pending_asset_is_409(guest_client: AsyncClient) -> None:
    asset = await create_pending_asset(guest_client)

    response = await post_job(guest_client, asset["asset_id"], "pending-asset-01")

    assert response.status_code == 409


async def test_another_users_asset_is_404(
    guest_client: AsyncClient,
    other_guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
) -> None:
    asset = await create_ready_asset(other_guest_client, object_storage)

    response = await post_job(guest_client, asset["asset_id"], "foreign-asset-01")

    assert response.status_code == 404


async def test_missing_idempotency_key_is_422(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)

    response = await guest_client.post(
        "/api/v1/jobs", json={"preset_slug": "dolly-in", "input_asset_id": asset["asset_id"]}
    )

    assert response.status_code == 422
