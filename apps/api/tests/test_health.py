from httpx import AsyncClient


async def test_health_reports_ok_when_database_is_up(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_health_reports_degraded_when_database_is_down(client_without_database: AsyncClient) -> None:
    response = await client_without_database.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}


async def test_unknown_api_path_is_not_served_as_spa(client: AsyncClient) -> None:
    response = await client.get("/api/does-not-exist")

    assert response.status_code == 404
