import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.asset import Asset
from app.models.job import Job
from app.models.job_sequence_clip import JobSequenceClip
from app.models.user import AppUser

CREATED_USER_IDS: list[uuid.UUID] = []


async def delete_created_rows(session: AsyncSession, user_ids: list[uuid.UUID]) -> None:
    job_ids = select(Job.id).where(Job.user_id.in_(user_ids))
    await session.execute(delete(JobSequenceClip).where(JobSequenceClip.job_id.in_(job_ids)))
    await session.execute(delete(Job).where(Job.user_id.in_(user_ids)))
    await session.execute(delete(Asset).where(Asset.user_id.in_(user_ids)))
    await session.execute(delete(AppUser).where(AppUser.id.in_(user_ids)))
    await session.commit()


@pytest.fixture(autouse=True)
async def remove_created_rows(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[None]:
    CREATED_USER_IDS.clear()
    yield
    if CREATED_USER_IDS:
        async with session_maker() as session:
            await delete_created_rows(session, list(CREATED_USER_IDS))


async def create_user(session_maker: async_sessionmaker[AsyncSession]) -> uuid.UUID:
    async with session_maker() as session:
        user = AppUser(is_guest=True)
        session.add(user)
        await session.commit()
        CREATED_USER_IDS.append(user.id)
        return user.id


async def create_asset(
    session_maker: async_sessionmaker[AsyncSession], user_id: uuid.UUID, kind: str
) -> uuid.UUID:
    content = "audio/mpeg" if kind == "input_audio" else "image/jpeg"
    async with session_maker() as session:
        asset = Asset(user_id=user_id, kind=kind, status="ready",
                      storage_key=f"tests/{uuid.uuid4().hex}.bin",
                      content_type=content, byte_size=16)
        session.add(asset)
        await session.commit()
        return asset.id


async def build_job(session_maker: async_sessionmaker[AsyncSession], **columns: object) -> uuid.UUID:
    async with session_maker() as session:
        job = Job(**columns)  # type: ignore[arg-type]
        session.add(job)
        await session.commit()
        return job.id


async def create_video_job(
    session_maker: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> uuid.UUID:
    asset_id = await create_asset(session_maker, user_id, "input_image")
    return await build_job(
        session_maker, user_id=user_id, kind="video", preset_slug="dolly-in",
        input_asset_id=asset_id, idempotency_key=uuid.uuid4().hex,
        status="queued", credit_cost=20,
    )


async def create_sequence_job(
    session_maker: async_sessionmaker[AsyncSession], user_id: uuid.UUID, **columns: object
) -> uuid.UUID:
    return await build_job(
        session_maker, user_id=user_id, kind="sequence", idempotency_key=uuid.uuid4().hex,
        status="queued", credit_cost=1, **columns,
    )


async def insert_clip(
    session_maker: async_sessionmaker[AsyncSession],
    job_id: uuid.UUID, source_id: uuid.UUID, position: int, transition: str,
) -> None:
    async with session_maker() as session:
        session.add(JobSequenceClip(job_id=job_id, source_job_id=source_id,
                                    position=position, transition_in=transition))
        await session.commit()


async def count_clips(session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID) -> int:
    async with session_maker() as session:
        found = await session.scalar(select(func.count()).select_from(JobSequenceClip)
                                     .where(JobSequenceClip.job_id == job_id))
        return int(found or 0)


async def test_sequence_job_with_two_clips_inserts(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await create_user(session_maker)
    first = await create_video_job(session_maker, user_id)
    second = await create_video_job(session_maker, user_id)
    job_id = await create_sequence_job(session_maker, user_id)
    await insert_clip(session_maker, job_id, first, 0, "cut")
    await insert_clip(session_maker, job_id, second, 1, "crossfade")

    assert await count_clips(session_maker, job_id) == 2


async def test_sequence_job_with_preset_slug_is_rejected(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await create_user(session_maker)

    with pytest.raises(IntegrityError):
        await create_sequence_job(session_maker, user_id, preset_slug="dolly-in")


async def test_video_job_with_audio_asset_is_rejected(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await create_user(session_maker)
    audio_id = await create_asset(session_maker, user_id, "input_audio")
    asset_id = await create_asset(session_maker, user_id, "input_image")

    with pytest.raises(IntegrityError):
        await build_job(session_maker, user_id=user_id, kind="video", preset_slug="dolly-in",
                         input_asset_id=asset_id, audio_asset_id=audio_id,
                         idempotency_key=uuid.uuid4().hex, status="queued", credit_cost=20)


async def test_unknown_transition_is_rejected(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await create_user(session_maker)
    source_id = await create_video_job(session_maker, user_id)
    job_id = await create_sequence_job(session_maker, user_id)

    with pytest.raises(IntegrityError):
        await insert_clip(session_maker, job_id, source_id, 0, "wipe")


async def test_position_six_is_rejected(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await create_user(session_maker)
    source_id = await create_video_job(session_maker, user_id)
    job_id = await create_sequence_job(session_maker, user_id)

    with pytest.raises(IntegrityError):
        await insert_clip(session_maker, job_id, source_id, 6, "cut")


async def test_zero_duration_is_rejected(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await create_user(session_maker)

    with pytest.raises(IntegrityError):
        await create_sequence_job(session_maker, user_id, duration_ms=0)


async def test_input_audio_asset_inserts(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await create_user(session_maker)

    assert await create_asset(session_maker, user_id, "input_audio") is not None


async def test_deleting_sequence_job_cascades_clips(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user_id = await create_user(session_maker)
    source_id = await create_video_job(session_maker, user_id)
    job_id = await create_sequence_job(session_maker, user_id)
    await insert_clip(session_maker, job_id, source_id, 0, "cut")

    async with session_maker() as session:
        job = await session.get(Job, job_id)
        assert job is not None
        await session.delete(job)
        await session.commit()

    assert await count_clips(session_maker, job_id) == 0
