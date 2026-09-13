from httpx import AsyncClient

from app.domain.credit_rules import GUEST_GRANT_CREDITS


async def test_credits_without_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/credits")

    assert response.status_code == 401
    assert response.json()["detail"]


async def test_fresh_guest_starts_with_the_grant(guest_client: AsyncClient) -> None:
    response = await guest_client.get("/api/v1/credits")

    assert response.status_code == 200
    assert response.json() == {"balance": GUEST_GRANT_CREDITS}


async def test_the_grant_is_written_once_per_guest(guest_client: AsyncClient) -> None:
    first = (await guest_client.get("/api/v1/credits")).json()["balance"]
    second = (await guest_client.get("/api/v1/credits")).json()["balance"]

    assert first == second == GUEST_GRANT_CREDITS
