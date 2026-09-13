import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.credit_rules import MAX_STEP_ATTEMPTS, release_amount
from app.domain.job_states import statuses_allowed_before
from app.repositories.job_steps import ExpiredStep, fail_step, lock_expired_steps, requeue_step
from app.repositories.jobs import notify_job_event, transition_job_status
from app.repositories.ledger import insert_ledger_entry

logger = logging.getLogger(__name__)

REAPER_BATCH_LIMIT = 20
FIRST_EXPIRY_ERROR = "lease expired"
SECOND_EXPIRY_ERROR = "lease expired twice"
TIMEOUT_USER_MESSAGE = "Generation timed out. Your credits were refunded."


async def reap_expired_steps(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    limit: int = REAPER_BATCH_LIMIT,
    max_step_attempts: int = MAX_STEP_ATTEMPTS,
) -> int:
    async with session_maker() as session:
        expired = await lock_expired_steps(session, limit)
        for step in expired:
            if step.attempt < max_step_attempts:
                await requeue_expired_step(session, step)
            else:
                await fail_expired_step(session, step)
            await notify_job_event(session, step.job_id)
        await session.commit()
    if expired:
        logger.info("reaper returned %s expired step(s) to the queue or failed them", len(expired))
    return len(expired)


async def requeue_expired_step(session: AsyncSession, step: ExpiredStep) -> None:
    await requeue_step(session, step.id, FIRST_EXPIRY_ERROR)
    await transition_job_status(
        session,
        step.job_id,
        "queued",
        allowed_from=statuses_allowed_before("queued"),
    )


async def fail_expired_step(session: AsyncSession, step: ExpiredStep) -> None:
    await fail_step(session, step.id, SECOND_EXPIRY_ERROR)
    await transition_job_status(
        session,
        step.job_id,
        "failed",
        allowed_from=statuses_allowed_before("failed"),
        error_message=TIMEOUT_USER_MESSAGE,
        finished_at=datetime.now(UTC),
    )
    await insert_ledger_entry(
        session,
        user_id=step.user_id,
        kind="RELEASE",
        amount=release_amount(step.credit_cost),
        job_id=step.job_id,
    )
