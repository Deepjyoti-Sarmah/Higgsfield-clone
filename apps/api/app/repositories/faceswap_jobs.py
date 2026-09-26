import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import asset, preset, user  # noqa: F401 (FK registration)
from app.models.job import Job


async def insert_faceswap_job(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    source_asset_id: uuid.UUID,
    target_asset_id: uuid.UUID,
    idempotency_key: str,
    credit_cost: int,
) -> Job:
    job = Job(
        user_id=user_id,
        kind="faceswap",
        preset_slug=None,
        input_asset_id=None,
        face_source_asset_id=source_asset_id,
        face_target_asset_id=target_asset_id,
        idempotency_key=idempotency_key,
        status="queued",
        credit_cost=credit_cost,
    )
    session.add(job)
    await session.flush()
    return job


async def find_owned_faceswap_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user_id, Job.kind == "faceswap")
    )
    return result.scalar_one_or_none()
