import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import asset, user  # noqa: F401 (FK registration)
from app.models.job import Job
from app.models.job_sequence_clip import JobSequenceClip


async def insert_sequence_job(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    audio_asset_id: uuid.UUID | None,
    idempotency_key: str,
    credit_cost: int,
) -> Job:
    job = Job(
        user_id=user_id,
        kind="sequence",
        audio_asset_id=audio_asset_id,
        idempotency_key=idempotency_key,
        status="queued",
        credit_cost=credit_cost,
    )
    session.add(job)
    await session.flush()
    return job


async def insert_sequence_clips(
    session: AsyncSession,
    job_id: uuid.UUID,
    clips: list[tuple[uuid.UUID, str, int, int | None]],
) -> None:
    for position, (source_id, transition, trim_start_ms, trim_end_ms) in enumerate(clips):
        session.add(
            JobSequenceClip(
                job_id=job_id,
                source_job_id=source_id,
                position=position,
                transition_in="cut" if position == 0 else transition,
                trim_start_ms=trim_start_ms,
                trim_end_ms=trim_end_ms,
            )
        )
    await session.flush()


async def find_clip_source_jobs(
    session: AsyncSession, user_id: uuid.UUID, job_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Job]:
    result = await session.execute(
        select(Job).where(Job.id.in_(job_ids), Job.user_id == user_id)
    )
    return {job.id: job for job in result.scalars()}


async def find_owned_sequence_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user_id, Job.kind == "sequence")
    )
    return result.scalar_one_or_none()


async def list_sequence_clips(
    session: AsyncSession, job_id: uuid.UUID
) -> list[tuple[JobSequenceClip, uuid.UUID | None]]:
    result = await session.execute(
        select(JobSequenceClip, Job.output_poster_asset_id)
        .join(Job, Job.id == JobSequenceClip.source_job_id)
        .where(JobSequenceClip.job_id == job_id)
        .order_by(JobSequenceClip.position)
    )
    return [(clip, poster_id) for clip, poster_id in result.all()]


async def count_clips_by_job(
    session: AsyncSession, job_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not job_ids:
        return {}
    result = await session.execute(
        select(JobSequenceClip.job_id, func.count())
        .where(JobSequenceClip.job_id.in_(job_ids))
        .group_by(JobSequenceClip.job_id)
    )
    return {row[0]: row[1] for row in result.all()}
