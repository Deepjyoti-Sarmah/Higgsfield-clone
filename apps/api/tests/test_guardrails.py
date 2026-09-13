import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.jobs import find_job
from app.services.guardrails import hash_client_ip
from app.settings import Settings, get_settings
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.fakes.scripted_model_adapter import ScriptedModelAdapter
from tests.job_api_helpers import create_ready_asset, post_job
from tests.worker_run_helpers import create_and_claim, run_video_step

GUEST_CAP_IP = "198.51.100.250"


async def test_sixth_guest_from_one_ip_is_rate_limited(
    client: AsyncClient, session_maker: async_sessionmaker[AsyncSession]
) -> None:
    ip_hash = hash_client_ip(GUEST_CAP_IP, get_settings().session_secret)
    async with session_maker() as session:
        await session.execute(
            text("DELETE FROM guest_issuance WHERE ip_hash = :ip_hash"), {"ip_hash": ip_hash}
        )
        await session.commit()
    headers = {"X-Forwarded-For": GUEST_CAP_IP}
    for _ in range(5):
        assert (await client.post("/api/v1/auth/guest", headers=headers)).status_code == 201
    blocked = await client.post("/api/v1/auth/guest", headers=headers)
    assert blocked.status_code == 429
    assert blocked.json() == {
        "detail": "Too many guest sessions from this address today.",
        "limit": 5,
        "used": 5,
    }


async def test_guest_ip_is_stored_only_as_a_hash(
    client: AsyncClient, session_maker: async_sessionmaker[AsyncSession]
) -> None:
    ip = f"203.0.113.{uuid.uuid4().int % 250 + 1}"
    created = await client.post("/api/v1/auth/guest", headers={"X-Forwarded-For": ip})
    assert created.status_code == 201
    async with session_maker() as session:
        hashes = list((await session.execute(text("SELECT ip_hash FROM guest_issuance"))).scalars())
    assert hash_client_ip(ip, get_settings().session_secret) in hashes
    assert all(ip not in stored for stored in hashes)


async def test_eleventh_job_in_a_day_is_rate_limited(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    assert (await guest_client.post("/api/v1/credits/topup")).status_code == 200
    assert (await guest_client.post("/api/v1/credits/topup")).status_code == 200
    asset = await create_ready_asset(guest_client, object_storage)
    for index in range(10):
        created = await post_job(guest_client, asset["asset_id"], f"daily-{index:04d}")
        assert created.status_code == 202, created.text
    blocked = await post_job(guest_client, asset["asset_id"], "daily-0011")
    assert blocked.status_code == 429
    assert blocked.json()["limit"] == 10 and blocked.json()["used"] == 10


async def test_third_topup_in_a_day_is_rate_limited(guest_client: AsyncClient) -> None:
    assert (await guest_client.post("/api/v1/credits/topup")).status_code == 200
    assert (await guest_client.post("/api/v1/credits/topup")).status_code == 200
    blocked = await guest_client.post("/api/v1/credits/topup")
    assert blocked.status_code == 429
    assert blocked.json()["limit"] == 2 and blocked.json()["used"] == 2


async def test_exhausted_budget_refuses_a_new_paid_job(
    app: object, guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(  # type: ignore[attr-defined]
        generation_backend="modal", paid_budget_cents=0
    )
    asset = await create_ready_asset(guest_client, object_storage)
    blocked = await post_job(guest_client, asset["asset_id"], "budget-0001")
    assert blocked.status_code == 429
    assert blocked.json()["budget_cents"] == 0


async def test_generated_by_is_exposed_on_job_and_library(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id, claimed = await create_and_claim(
        guest_client, object_storage, session_maker, "label-0001"
    )
    await run_video_step(session_maker, object_storage, claimed, ScriptedModelAdapter())
    async with session_maker() as session:
        job = await find_job(session, job_id)
    assert job is not None and job.generated_by == "scripted"
    detail = await guest_client.get(f"/api/v1/jobs/{job_id}")
    assert detail.status_code == 200
    assert detail.json()["generated_by"] == "scripted"
    library = await guest_client.get("/api/v1/jobs")
    items = library.json()["items"]
    assert any(item["id"] == str(job_id) and item["generated_by"] == "scripted" for item in items)
