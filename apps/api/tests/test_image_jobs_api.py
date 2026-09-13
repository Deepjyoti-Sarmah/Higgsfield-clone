import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.image_rules import IMAGE_CREDIT_COST_HIGH, IMAGE_CREDIT_COST_STANDARD
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import GUEST_GRANT, balance_of, create_queued_job, current_user_id

SessionMaker = async_sessionmaker[AsyncSession]


def _body(
    key: str, *, quality: str = "standard", count: int = 1, prompt: str = "a cat"
) -> dict[str, object]:
    return {
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "quality": quality,
        "count": count,
        "idempotency_key": key,
    }


async def test_image_routes_need_a_cookie(client: AsyncClient) -> None:
    created = await client.post("/api/v1/image-jobs", json=_body("t009-anon-01"))
    read = await client.get(f"/api/v1/image-jobs/{uuid.uuid4()}")

    assert created.status_code == 401
    assert read.status_code == 401


async def test_create_holds_the_credit_cost_and_reads_back(guest_client: AsyncClient) -> None:
    created = await guest_client.post("/api/v1/image-jobs", json=_body("t009-create-01"))

    assert created.status_code == 202
    body = created.json()
    assert body["status"] == "queued"
    assert body["credit_cost"] == IMAGE_CREDIT_COST_STANDARD
    assert body["image_count"] == 1
    assert await balance_of(guest_client) == GUEST_GRANT - IMAGE_CREDIT_COST_STANDARD

    read = await guest_client.get(f"/api/v1/image-jobs/{body['id']}")
    assert read.status_code == 200
    assert read.json()["prompt"] == "a cat"
    assert read.json()["image_urls"] == []
    assert read.json()["backend"] is None


async def test_one_hold_row_is_written_per_job(
    guest_client: AsyncClient, session_maker: SessionMaker
) -> None:
    user_id = await current_user_id(guest_client)

    await guest_client.post("/api/v1/image-jobs", json=_body("t009-hold-01"))

    async with session_maker() as session:
        holds = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE user_id = :id AND kind = 'HOLD'"),
            {"id": uuid.UUID(user_id)},
        )
    assert holds == 1


async def test_the_same_key_returns_the_same_job_and_holds_once(guest_client: AsyncClient) -> None:
    body = _body("t009-idem-01")

    first = await guest_client.post("/api/v1/image-jobs", json=body)
    second = await guest_client.post("/api/v1/image-jobs", json=body)

    assert first.status_code == second.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert await balance_of(guest_client) == GUEST_GRANT - IMAGE_CREDIT_COST_STANDARD


async def test_four_high_quality_images_cost_the_whole_grant_then_402(
    guest_client: AsyncClient,
) -> None:
    full = IMAGE_CREDIT_COST_HIGH * 4

    first = await guest_client.post(
        "/api/v1/image-jobs", json=_body("t009-max-01", quality="high", count=4)
    )
    assert first.status_code == 202
    assert first.json()["credit_cost"] == full == GUEST_GRANT
    assert await balance_of(guest_client) == 0

    second = await guest_client.post(
        "/api/v1/image-jobs", json=_body("t009-max-02", quality="high", count=4)
    )
    assert second.status_code == 402
    assert second.json() == {"detail": "Not enough credits", "balance": 0, "required": full}


async def test_an_image_job_is_not_the_video_read_and_is_owner_scoped(
    guest_client: AsyncClient, other_guest_client: AsyncClient
) -> None:
    created = await guest_client.post("/api/v1/image-jobs", json=_body("t009-scope-01"))
    job_id = created.json()["id"]

    video_read = await guest_client.get(f"/api/v1/jobs/{job_id}")
    stranger = await other_guest_client.get(f"/api/v1/image-jobs/{job_id}")
    owner = await guest_client.get(f"/api/v1/image-jobs/{job_id}")

    assert video_read.status_code == 404
    assert stranger.status_code == 404
    assert owner.status_code == 200


async def test_an_idempotency_key_cannot_cross_job_types(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    key = "t009-cross-0001"
    await create_queued_job(guest_client, object_storage, key)

    response = await guest_client.post("/api/v1/image-jobs", json=_body(key))

    assert response.status_code == 422


async def test_invalid_settings_are_rejected(guest_client: AsyncClient) -> None:
    bad_ratio = {**_body("t009-bad-01"), "aspect_ratio": "2:1"}
    bad_count = _body("t009-bad-02", count=5)
    empty_prompt = _body("t009-bad-03", prompt="")

    assert (await guest_client.post("/api/v1/image-jobs", json=bad_ratio)).status_code == 422
    assert (await guest_client.post("/api/v1/image-jobs", json=bad_count)).status_code == 422
    assert (await guest_client.post("/api/v1/image-jobs", json=empty_prompt)).status_code == 422
