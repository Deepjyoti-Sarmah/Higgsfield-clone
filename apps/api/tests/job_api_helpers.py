import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.fakes.in_memory_object_storage import InMemoryObjectStorage

JPEG_BYTES = b"\xff\xd8\xff" + b"0" * 300
PRESET_SLUG = "dolly-in"
PRESET_COST = 20
GUEST_GRANT = 60
PRESET_NAME = "Dolly In"


async def current_user_id(http_client: AsyncClient) -> str:
    me = await http_client.get("/api/v1/me")
    assert me.status_code == 200
    return str(me.json()["id"])


async def create_ready_asset(
    http_client: AsyncClient, storage: InMemoryObjectStorage
) -> dict[str, str]:
    created = await http_client.post(
        "/api/v1/uploads", json={"content_type": "image/jpeg", "byte_size": len(JPEG_BYTES)}
    )
    assert created.status_code == 201
    upload = created.json()
    key = f"users/{await current_user_id(http_client)}/inputs/{upload['asset_id']}.jpg"
    storage.put_bytes(key, JPEG_BYTES)
    completed = await http_client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")
    assert completed.status_code == 200
    return upload


async def create_pending_asset(http_client: AsyncClient) -> dict[str, str]:
    created = await http_client.post(
        "/api/v1/uploads", json={"content_type": "image/jpeg", "byte_size": len(JPEG_BYTES)}
    )
    assert created.status_code == 201
    return created.json()


async def post_job(
    http_client: AsyncClient,
    asset_id: str,
    key: str,
    *,
    slug: str = PRESET_SLUG,
    prompt: str | None = "slow push in",
) -> object:
    return await http_client.post(
        "/api/v1/jobs",
        json={
            "preset_slug": slug,
            "input_asset_id": asset_id,
            "prompt": prompt,
            "idempotency_key": key,
        },
    )


async def create_queued_job(
    http_client: AsyncClient, storage: InMemoryObjectStorage, key: str
) -> str:
    asset = await create_ready_asset(http_client, storage)
    created = await post_job(http_client, asset["asset_id"], key)
    assert created.status_code == 202
    return str(created.json()["id"])


async def balance_of(http_client: AsyncClient) -> int:
    response = await http_client.get("/api/v1/credits")
    assert response.status_code == 200
    return int(response.json()["balance"])


async def count_job_rows(
    session_maker: async_sessionmaker[AsyncSession], table: str, job_id: uuid.UUID
) -> int:
    key_column = "id" if table == "job" else "job_id"
    statement = text(f"SELECT count(*) FROM {table} WHERE {key_column} = :job_id")
    async with session_maker() as session:
        return int(await session.scalar(statement, {"job_id": job_id}) or 0)
