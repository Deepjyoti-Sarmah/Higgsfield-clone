import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.credit_rules import release_amount
from app.domain.job_states import statuses_allowed_before
from app.repositories.assets import insert_asset
from app.repositories.job_steps import finish_step
from app.repositories.jobs import find_job, notify_job_event, transition_job_status
from app.repositories.ledger import insert_ledger_entry

VIDEO_CONTENT_TYPE = "video/mp4"
POSTER_CONTENT_TYPE = "image/jpeg"


async def complete_step_success(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    step_id: uuid.UUID,
    job_id: uuid.UUID,
    worker_id: str,
    backend: str,
    video_key: str,
    poster_key: str,
    video_size: int,
    poster_size: int,
) -> bool:
    async with session_maker() as session:
        if not await finish_step(session, step_id, worker_id, "succeeded", backend=backend):
            # The lease was reaped: another worker owns the job now, so write nothing.
            await session.rollback()
            return False
        job = await find_job(session, job_id)
        if job is None:
            await session.rollback()
            return False
        video_asset_id = uuid.uuid4()
        poster_asset_id = uuid.uuid4()
        await insert_asset(
            session,
            asset_id=video_asset_id,
            user_id=job.user_id,
            kind="output_video",
            status="ready",
            storage_key=video_key,
            content_type=VIDEO_CONTENT_TYPE,
            byte_size=video_size,
        )
        await insert_asset(
            session,
            asset_id=poster_asset_id,
            user_id=job.user_id,
            kind="output_poster",
            status="ready",
            storage_key=poster_key,
            content_type=POSTER_CONTENT_TYPE,
            byte_size=poster_size,
        )
        succeeded = await transition_job_status(
            session,
            job_id,
            "succeeded",
            allowed_from=statuses_allowed_before("succeeded"),
            output_video_asset_id=video_asset_id,
            output_poster_asset_id=poster_asset_id,
            finished_at=datetime.now(UTC),
        )
        if not succeeded:
            await session.rollback()
            return False
        await insert_ledger_entry(
            session, user_id=job.user_id, kind="SETTLE", amount=0, job_id=job_id
        )
        await notify_job_event(session, job_id)
        await session.commit()
        return True


async def complete_step_failure(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    step_id: uuid.UUID,
    job_id: uuid.UUID,
    worker_id: str,
    backend: str,
    last_error: str,
    user_message: str,
) -> bool:
    async with session_maker() as session:
        if not await finish_step(
            session, step_id, worker_id, "failed", backend=backend, last_error=last_error
        ):
            await session.rollback()
            return False
        job = await find_job(session, job_id)
        if job is None:
            await session.rollback()
            return False
        failed = await transition_job_status(
            session,
            job_id,
            "failed",
            allowed_from=statuses_allowed_before("failed"),
            error_message=user_message,
            finished_at=datetime.now(UTC),
        )
        if not failed:
            await session.rollback()
            return False
        await insert_ledger_entry(
            session,
            user_id=job.user_id,
            kind="RELEASE",
            amount=release_amount(job.credit_cost),
            job_id=job_id,
        )
        await notify_job_event(session, job_id)
        await session.commit()
        return True
