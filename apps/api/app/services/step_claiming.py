import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.job_states import TERMINAL_STATUSES, statuses_allowed_before
from app.repositories.job_steps import ClaimedStep, claim_next_queued_step, fail_step
from app.repositories.jobs import notify_job_event, read_job_status, transition_job_status

logger = logging.getLogger(__name__)

TERMINAL_JOB_ERROR = "job already terminal"


async def claim_step(
    session_maker: async_sessionmaker[AsyncSession],
    worker_id: str,
    lease_seconds: int,
) -> ClaimedStep | None:
    async with session_maker() as session:
        claimed = await claim_next_queued_step(session, worker_id, lease_seconds)
        if claimed is None:
            return None
        if await read_job_status(session, claimed.job_id) in TERMINAL_STATUSES:
            # Nothing can consume this row again, and leaving it queued would starve the loop.
            await session.rollback()
            await abandon_step(session_maker, claimed.id)
            return None
        await transition_job_status(
            session,
            claimed.job_id,
            "running",
            allowed_from=statuses_allowed_before("running"),
            started_at=datetime.now(UTC),
        )
        await notify_job_event(session, claimed.job_id)
        await session.commit()
        return claimed


async def abandon_step(session_maker: async_sessionmaker[AsyncSession], step_id: uuid.UUID) -> None:
    logger.warning("abandoning step %s: its job is already terminal", step_id)
    async with session_maker() as session:
        await fail_step(session, step_id, TERMINAL_JOB_ERROR)
        await session.commit()
