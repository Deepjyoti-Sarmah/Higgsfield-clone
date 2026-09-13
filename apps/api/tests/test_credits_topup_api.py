import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.credit_rules import GUEST_GRANT_CREDITS, TOPUP_CREDITS
from tests.job_api_helpers import current_user_id


async def _ledger_rows(
    session_maker: async_sessionmaker[AsyncSession], user_id: str, kind: str
) -> list[tuple[int, object]]:
    async with session_maker() as session:
        result = await session.execute(
            text(
                "SELECT amount, job_id FROM ledger_entry"
                " WHERE user_id = :user_id AND kind = :kind"
            ),
            {"user_id": uuid.UUID(user_id), "kind": kind},
        )
        return [(row.amount, row.job_id) for row in result]


async def test_topup_without_a_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.post("/api/v1/credits/topup")

    assert response.status_code == 401
    assert response.json()["detail"]


async def test_topup_grants_the_fixed_amount_and_returns_the_new_balance(
    guest_client: AsyncClient,
) -> None:
    before = (await guest_client.get("/api/v1/credits")).json()
    assert before == {"balance": GUEST_GRANT_CREDITS}

    response = await guest_client.post("/api/v1/credits/topup")

    assert response.status_code == 200
    assert response.json() == {"amount": TOPUP_CREDITS, "balance": GUEST_GRANT_CREDITS + TOPUP_CREDITS}
    after = (await guest_client.get("/api/v1/credits")).json()
    assert after == {"balance": GUEST_GRANT_CREDITS + TOPUP_CREDITS}


async def test_topup_is_repeatable(guest_client: AsyncClient) -> None:
    first = (await guest_client.post("/api/v1/credits/topup")).json()
    second = (await guest_client.post("/api/v1/credits/topup")).json()

    assert first == {"amount": TOPUP_CREDITS, "balance": GUEST_GRANT_CREDITS + TOPUP_CREDITS}
    assert second == {"amount": TOPUP_CREDITS, "balance": GUEST_GRANT_CREDITS + 2 * TOPUP_CREDITS}


async def test_each_topup_writes_one_jobless_topup_row(
    guest_client: AsyncClient, session_maker: async_sessionmaker[AsyncSession]
) -> None:
    user_id = await current_user_id(guest_client)

    await guest_client.post("/api/v1/credits/topup")
    await guest_client.post("/api/v1/credits/topup")

    rows = await _ledger_rows(session_maker, user_id, "TOPUP")

    assert rows == [(TOPUP_CREDITS, None), (TOPUP_CREDITS, None)]


async def test_topup_leaves_the_one_time_guest_grant_untouched(
    guest_client: AsyncClient, session_maker: async_sessionmaker[AsyncSession]
) -> None:
    user_id = await current_user_id(guest_client)

    await guest_client.post("/api/v1/credits/topup")

    grants = await _ledger_rows(session_maker, user_id, "GRANT")

    assert grants == [(GUEST_GRANT_CREDITS, None)]
