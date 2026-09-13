import json
import uuid
from collections.abc import Collection
from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.job_states import JobStatus
from app.models import asset, job_step, ledger_entry, preset, user  # noqa: F401 (FK registration)
from app.models.job import Job


async def find_job_by_idempotency_key(
    session: AsyncSession, user_id: uuid.UUID, key: str
) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.user_id == user_id, Job.idempotency_key == key)
    )
    return result.scalar_one_or_none()


async def insert_job(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    preset_slug: str,
    input_asset_id: uuid.UUID,
    prompt: str | None,
    idempotency_key: str,
    credit_cost: int,
) -> Job:
    job = Job(
        user_id=user_id,
        preset_slug=preset_slug,
        input_asset_id=input_asset_id,
        prompt=prompt,
        idempotency_key=idempotency_key,
        status="queued",
        credit_cost=credit_cost,
    )
    session.add(job)
    await session.flush()
    return job


async def find_user_job(session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> Job | None:
    result = await session.execute(select(Job).where(Job.id == job_id, Job.user_id == user_id))
    return result.scalar_one_or_none()


async def find_job(session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    return await session.get(Job, job_id)


async def read_job_status(session: AsyncSession, job_id: uuid.UUID) -> str | None:
    return await session.scalar(select(Job.status).where(Job.id == job_id))


async def transition_job_status(
    session: AsyncSession,
    job_id: uuid.UUID,
    to_status: JobStatus,
    *,
    allowed_from: Collection[str],
    error_message: str | None = None,
    output_video_asset_id: uuid.UUID | None = None,
    output_poster_asset_id: uuid.UUID | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> bool:
    values: dict[str, Any] = {"status": to_status, "updated_at": func.now()}
    optional: dict[str, Any] = {
        "error_message": error_message,
        "output_video_asset_id": output_video_asset_id,
        "output_poster_asset_id": output_poster_asset_id,
        "started_at": started_at,
        "finished_at": finished_at,
    }
    values.update({name: value for name, value in optional.items() if value is not None})
    statement = update(Job).where(Job.id == job_id, Job.status.in_(allowed_from)).values(**values)
    result = cast(CursorResult[Any], await session.execute(statement))
    return result.rowcount > 0


async def notify_job_event(session: AsyncSession, job_id: uuid.UUID) -> None:
    payload = json.dumps({"job_id": str(job_id)})
    await session.execute(text("SELECT pg_notify('job_events', :payload)"), {"payload": payload})
