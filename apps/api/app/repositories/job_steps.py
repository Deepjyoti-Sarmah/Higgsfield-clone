import uuid
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import CursorResult, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import asset, job, ledger_entry, preset, user  # noqa: F401 (FK registration)
from app.models.job_step import JobStep


@dataclass(frozen=True)
class ClaimedStep:
    id: uuid.UUID
    job_id: uuid.UUID
    kind: str
    attempt: int


@dataclass(frozen=True)
class ExpiredStep:
    id: uuid.UUID
    job_id: uuid.UUID
    attempt: int
    user_id: uuid.UUID
    credit_cost: int


CLAIM_STEP_SQL = text(
    """
    UPDATE job_step
    SET status = 'running', attempt = attempt + 1, lease_owner = :worker_id,
        lease_expires_at = now() + make_interval(secs => :lease_seconds),
        started_at = coalesce(started_at, now()), updated_at = now()
    WHERE id = (
      SELECT id FROM job_step
      WHERE status = 'queued'
      ORDER BY created_at
      LIMIT 1
      FOR UPDATE SKIP LOCKED
    )
    RETURNING id, job_id, kind, attempt
    """
)

RENEW_LEASE_SQL = text(
    """
    UPDATE job_step
    SET lease_expires_at = now() + make_interval(secs => :lease_seconds), updated_at = now()
    WHERE id = :step_id AND lease_owner = :worker_id AND status = 'running'
    """
)

FINISH_STEP_SQL = text(
    """
    UPDATE job_step
    SET status = :to_status, finished_at = now(), lease_owner = NULL, lease_expires_at = NULL,
        backend = :backend, last_error = :last_error, updated_at = now()
    WHERE id = :step_id AND lease_owner = :worker_id AND status = 'running'
    """
)

LOCK_EXPIRED_SQL = text(
    """
    SELECT s.id, s.job_id, s.attempt, j.user_id, j.credit_cost
    FROM job_step s JOIN job j ON j.id = s.job_id
    WHERE s.status = 'running' AND s.lease_expires_at < now()
    ORDER BY s.lease_expires_at
    LIMIT :limit
    FOR UPDATE OF s SKIP LOCKED
    """
)

REQUEUE_STEP_SQL = text(
    """
    UPDATE job_step
    SET status = 'queued', lease_owner = NULL, lease_expires_at = NULL,
        last_error = :last_error, updated_at = now()
    WHERE id = :step_id
    """
)

FAIL_STEP_SQL = text(
    """
    UPDATE job_step
    SET status = 'failed', finished_at = now(), last_error = :last_error, updated_at = now()
    WHERE id = :step_id
    """
)


async def insert_job_step(session: AsyncSession, job_id: uuid.UUID, kind: str) -> JobStep:
    step = JobStep(job_id=job_id, kind=kind, status="queued")
    session.add(step)
    await session.flush()
    return step


async def claim_next_queued_step(
    session: AsyncSession, worker_id: str, lease_seconds: int
) -> ClaimedStep | None:
    result = await session.execute(
        CLAIM_STEP_SQL, {"worker_id": worker_id, "lease_seconds": lease_seconds}
    )
    row = result.first()
    if row is None:
        return None
    return ClaimedStep(id=row.id, job_id=row.job_id, kind=row.kind, attempt=row.attempt)


async def renew_step_lease(
    session: AsyncSession, step_id: uuid.UUID, worker_id: str, lease_seconds: int
) -> bool:
    result = cast(
        CursorResult[Any],
        await session.execute(
            RENEW_LEASE_SQL,
            {"step_id": step_id, "worker_id": worker_id, "lease_seconds": lease_seconds},
        ),
    )
    return result.rowcount > 0


async def finish_step(
    session: AsyncSession,
    step_id: uuid.UUID,
    worker_id: str,
    to_status: str,
    *,
    backend: str,
    last_error: str | None = None,
) -> bool:
    result = cast(
        CursorResult[Any],
        await session.execute(
            FINISH_STEP_SQL,
            {
                "step_id": step_id,
                "worker_id": worker_id,
                "to_status": to_status,
                "backend": backend,
                "last_error": last_error,
            },
        ),
    )
    return result.rowcount > 0


async def lock_expired_steps(session: AsyncSession, limit: int) -> list[ExpiredStep]:
    result = await session.execute(LOCK_EXPIRED_SQL, {"limit": limit})
    return [
        ExpiredStep(
            id=row.id,
            job_id=row.job_id,
            attempt=row.attempt,
            user_id=row.user_id,
            credit_cost=row.credit_cost,
        )
        for row in result
    ]


async def requeue_step(session: AsyncSession, step_id: uuid.UUID, last_error: str) -> None:
    await session.execute(REQUEUE_STEP_SQL, {"step_id": step_id, "last_error": last_error})


async def fail_step(session: AsyncSession, step_id: uuid.UUID, last_error: str) -> None:
    await session.execute(FAIL_STEP_SQL, {"step_id": step_id, "last_error": last_error})
