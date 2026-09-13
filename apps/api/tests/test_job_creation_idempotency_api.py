import asyncio
import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import (
    GUEST_GRANT,
    PRESET_COST,
    balance_of,
    count_job_rows,
    create_ready_asset,
    post_job,
)


async def test_same_idempotency_key_returns_the_same_job_with_one_hold(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)

    first = await post_job(guest_client, asset["asset_id"], "repeat-key-0001")
    second = await post_job(guest_client, asset["asset_id"], "repeat-key-0001")

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    job_id = uuid.UUID(first.json()["id"])
    assert await count_job_rows(session_maker, "job", job_id) == 1
    assert await count_job_rows(session_maker, "ledger_entry", job_id) == 1
    assert await balance_of(guest_client) == GUEST_GRANT - PRESET_COST


async def test_concurrent_same_key_creates_one_job_with_one_hold(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)

    responses = await asyncio.gather(
        post_job(guest_client, asset["asset_id"], "parallel-key-0001"),
        post_job(guest_client, asset["asset_id"], "parallel-key-0001"),
    )

    assert [response.status_code for response in responses] == [202, 202]
    ids = {response.json()["id"] for response in responses}
    assert len(ids) == 1
    assert await count_job_rows(session_maker, "job", uuid.UUID(ids.pop())) == 1
    assert await balance_of(guest_client) == GUEST_GRANT - PRESET_COST


async def test_a_different_key_with_the_same_body_is_a_second_job(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    asset = await create_ready_asset(guest_client, object_storage)

    first = await post_job(guest_client, asset["asset_id"], "distinct-key-0001")
    second = await post_job(guest_client, asset["asset_id"], "distinct-key-0002")

    assert first.json()["id"] != second.json()["id"]
    assert await count_job_rows(session_maker, "ledger_entry", uuid.UUID(first.json()["id"])) == 1
    assert await count_job_rows(session_maker, "ledger_entry", uuid.UUID(second.json()["id"])) == 1
    assert await balance_of(guest_client) == GUEST_GRANT - 2 * PRESET_COST
