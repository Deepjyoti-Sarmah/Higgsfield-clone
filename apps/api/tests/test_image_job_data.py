import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.job import Job
from app.repositories.assets import insert_asset
from app.repositories.image_jobs import (
    find_owned_image_job,
    insert_image_job,
    insert_job_image,
    list_job_images,
)
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import create_queued_job, current_user_id

SessionMaker = async_sessionmaker[AsyncSession]
PRESET_SLUG = "dolly-in"


async def _create_image_job(session_maker: SessionMaker, user_id: str, key: str) -> Job:
    async with session_maker() as session:
        job = await insert_image_job(
            session,
            user_id=uuid.UUID(user_id),
            prompt="a cat on a skateboard",
            aspect_ratio="16:9",
            quality="standard",
            image_count=2,
            idempotency_key=key,
            credit_cost=20,
        )
        await session.commit()
        return job


async def _insert_output_image(session_maker: SessionMaker, user_id: str, name: str) -> uuid.UUID:
    asset_id = uuid.uuid4()
    async with session_maker() as session:
        await insert_asset(
            session,
            asset_id=asset_id,
            user_id=uuid.UUID(user_id),
            kind="output_image",
            status="ready",
            storage_key=f"users/{user_id}/jobs/{name}.png",
            content_type="image/png",
            byte_size=1234,
        )
        await session.commit()
    return asset_id


def _image_job_fields(user_id: uuid.UUID, key: str, **overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "user_id": user_id,
        "kind": "image",
        "prompt": "x",
        "aspect_ratio": "1:1",
        "quality": "high",
        "image_count": 1,
        "idempotency_key": key,
        "status": "queued",
        "credit_cost": 10,
    }
    fields.update(overrides)
    return fields


async def _flush_job(session_maker: SessionMaker, **columns: object) -> None:
    async with session_maker() as session:
        session.add(Job(**columns))
        await session.flush()
        await session.commit()


async def test_a_video_job_still_round_trips_through_the_api(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "t009-video-01")

    listing = await guest_client.get("/api/v1/jobs")
    read = await guest_client.get(f"/api/v1/jobs/{job_id}")

    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [job_id]
    assert read.status_code == 200
    assert read.json()["preset_slug"] == PRESET_SLUG


async def test_an_image_job_appears_in_the_library_but_not_the_video_read(
    guest_client: AsyncClient, session_maker: SessionMaker
) -> None:
    # T-038: the Library is kind-agnostic (this test used to assert the opposite —
    # that was root cause #2 of the image-generation-invisible bug). The video-only
    # single-job read at GET /jobs/{id} is unchanged: it still 404s for an image job.
    user_id = await current_user_id(guest_client)
    job = await _create_image_job(session_maker, user_id, "t009-image-01")

    listing = await guest_client.get("/api/v1/jobs")
    read = await guest_client.get(f"/api/v1/jobs/{job.id}")

    assert listing.status_code == 200
    item = listing.json()["items"][0]
    assert item["id"] == str(job.id)
    assert item["kind"] == "image"
    assert read.status_code == 404


async def test_an_image_job_round_trips_with_its_outputs(
    guest_client: AsyncClient, session_maker: SessionMaker
) -> None:
    user_id = await current_user_id(guest_client)
    job = await _create_image_job(session_maker, user_id, "t009-image-02")
    first = await _insert_output_image(session_maker, user_id, "t009-out-a")
    second = await _insert_output_image(session_maker, user_id, "t009-out-b")

    async with session_maker() as session:
        await insert_job_image(session, job_id=job.id, position=1, asset_id=first)
        await insert_job_image(session, job_id=job.id, position=2, asset_id=second)
        await session.commit()
    async with session_maker() as session:
        found = await find_owned_image_job(session, uuid.UUID(user_id), job.id)
        images = await list_job_images(session, job.id)

    assert found is not None
    assert found.kind == "image"
    assert found.preset_slug is None and found.input_asset_id is None
    assert (found.aspect_ratio, found.quality, found.image_count) == ("16:9", "standard", 2)
    assert [image.position for image in images] == [1, 2]
    assert [image.asset_id for image in images] == [first, second]


async def test_an_image_job_is_owner_scoped(
    guest_client: AsyncClient, other_guest_client: AsyncClient, session_maker: SessionMaker
) -> None:
    user_id = await current_user_id(guest_client)
    other_id = await current_user_id(other_guest_client)
    job = await _create_image_job(session_maker, user_id, "t009-image-03")

    async with session_maker() as session:
        mine = await find_owned_image_job(session, uuid.UUID(user_id), job.id)
        theirs = await find_owned_image_job(session, uuid.UUID(other_id), job.id)

    assert mine is not None
    assert theirs is None


async def test_a_video_job_without_a_preset_or_input_is_rejected(
    guest_client: AsyncClient, session_maker: SessionMaker
) -> None:
    user_id = uuid.UUID(await current_user_id(guest_client))
    fields = _image_job_fields(
        user_id,
        "t009-bad-video",
        kind="video",
        preset_slug=None,
        input_asset_id=None,
        aspect_ratio=None,
        quality=None,
        image_count=None,
    )
    with pytest.raises(IntegrityError):
        await _flush_job(session_maker, **fields)


async def test_an_image_job_with_a_preset_is_rejected(
    guest_client: AsyncClient, session_maker: SessionMaker
) -> None:
    user_id = uuid.UUID(await current_user_id(guest_client))
    fields = _image_job_fields(user_id, "t009-bad-image", preset_slug=PRESET_SLUG)
    with pytest.raises(IntegrityError):
        await _flush_job(session_maker, **fields)


@pytest.mark.parametrize("count", [0, 5])
async def test_an_image_count_outside_one_to_four_is_rejected(
    guest_client: AsyncClient, session_maker: SessionMaker, count: int
) -> None:
    user_id = uuid.UUID(await current_user_id(guest_client))
    fields = _image_job_fields(user_id, f"t009-bad-count-{count}", image_count=count)
    with pytest.raises(IntegrityError):
        await _flush_job(session_maker, **fields)


async def test_an_image_job_without_params_is_rejected(
    guest_client: AsyncClient, session_maker: SessionMaker
) -> None:
    user_id = uuid.UUID(await current_user_id(guest_client))
    fields = _image_job_fields(
        user_id, "t009-bad-params", aspect_ratio=None, quality=None, image_count=None
    )
    with pytest.raises(IntegrityError):
        await _flush_job(session_maker, **fields)
