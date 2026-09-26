import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import asset, preset, user  # noqa: F401 (FK registration)
from app.models.job import Job


async def insert_video_faceswap_job(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    source_asset_id: uuid.UUID,
    target_asset_id: uuid.UUID,
    idempotency_key: str,
    credit_cost: int,
    duration_ms: int,
) -> Job:
    job = Job(
        user_id=user_id,
        kind="video_faceswap",
        preset_slug=None,
        input_asset_id=None,
        face_source_asset_id=source_asset_id,
        face_target_asset_id=target_asset_id,
        idempotency_key=idempotency_key,
        status="queued",
        credit_cost=credit_cost,
        duration_ms=duration_ms,
    )
    session.add(job)
    await session.flush()
    return job


async def find_owned_video_faceswap_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user_id, Job.kind == "video_faceswap")
    )
    return result.scalar_one_or_none()


async def find_owned_target_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Job | None:
    """Owner-scoped, kind-agnostic: the service maps foreign/missing to 404."""
    result = await session.execute(select(Job).where(Job.id == job_id, Job.user_id == user_id))
    return result.scalar_one_or_none()


async def find_owned_video_producer(
    session: AsyncSession, user_id: uuid.UUID, asset_id: uuid.UUID
) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.output_video_asset_id == asset_id, Job.user_id == user_id)
    )
    return result.scalar_one_or_none()
