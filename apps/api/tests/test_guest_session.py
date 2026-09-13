import uuid

from httpx import AsyncClient

from app.services.session_tokens import sign_session_token
from app.settings import get_settings


async def test_me_without_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")

    assert response.status_code == 401


async def test_guest_session_is_created_and_persists(client: AsyncClient) -> None:
    headers = {"X-Forwarded-For": f"test-{uuid.uuid4()}"}
    created = await client.post("/api/v1/auth/guest", headers=headers)

    assert created.status_code == 201
    assert created.json()["is_guest"] is True
    set_cookie = created.headers["set-cookie"].lower()
    assert "httponly" in set_cookie and "samesite=lax" in set_cookie

    me = await client.get("/api/v1/me")
    assert me.status_code == 200
    assert me.json()["id"] == created.json()["id"]


async def test_tampered_session_cookie_is_unauthorized(client: AsyncClient) -> None:
    client.cookies.set("session", "not-a-real-token")

    response = await client.get("/api/v1/me")

    assert response.status_code == 401


async def test_token_for_missing_user_is_unauthorized(client: AsyncClient) -> None:
    settings = get_settings()
    token = sign_session_token("00000000-0000-0000-0000-000000000000", settings.session_secret, 1)  # type: ignore[arg-type]
    client.cookies.set("session", token)

    response = await client.get("/api/v1/me")

    assert response.status_code == 401
