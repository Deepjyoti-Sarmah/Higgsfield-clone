import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import asset, preset, user  # noqa: F401 (FK registration)
from app.models.job import Job
from app.models.job_image import JobImage
from app.models.job_step import JobStep


async def insert_image_job(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    prompt: str,
    aspect_ratio: str,
    quality: str,
    image_count: int,
    idempotency_key: str,
    credit_cost: int,
) -> Job:
    job = Job(
        user_id=user_id,
        kind="image",
        preset_slug=None,
        input_asset_id=None,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        quality=quality,
        image_count=image_count,
        idempotency_key=idempotency_key,
        status="queued",
        credit_cost=credit_cost,
    )
    session.add(job)
    await session.flush()
    return job


async def insert_job_image(
    session: AsyncSession, *, job_id: uuid.UUID, position: int, asset_id: uuid.UUID
) -> JobImage:
    image = JobImage(job_id=job_id, position=position, asset_id=asset_id)
    session.add(image)
    await session.flush()
    return image


async def list_job_images(session: AsyncSession, job_id: uuid.UUID) -> list[JobImage]:
    result = await session.execute(
        select(JobImage).where(JobImage.job_id == job_id).order_by(JobImage.position)
    )
    return list(result.scalars())


async def find_owned_image_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user_id, Job.kind == "image")
    )
    return result.scalar_one_or_none()


async def find_job_backend(session: AsyncSession, job_id: uuid.UUID) -> str | None:
    return cast(
        "str | None",
        await session.scalar(select(JobStep.backend).where(JobStep.job_id == job_id)),
    )
