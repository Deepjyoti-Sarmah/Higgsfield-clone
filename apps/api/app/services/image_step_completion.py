import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.job_states import statuses_allowed_before
from app.repositories.assets import insert_asset
from app.repositories.image_jobs import insert_job_image
from app.repositories.job_steps import finish_step
from app.repositories.jobs import find_job, notify_job_event, transition_job_status
from app.repositories.ledger import insert_ledger_entry

IMAGE_CONTENT_TYPE = "image/png"


async def complete_image_step_success(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    step_id: uuid.UUID,
    job_id: uuid.UUID,
    worker_id: str,
    backend: str,
    images: list[tuple[int, str, int]],
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
        for position, storage_key, byte_size in images:
            asset_id = uuid.uuid4()
            await insert_asset(
                session,
                asset_id=asset_id,
                user_id=job.user_id,
                kind="output_image",
                status="ready",
                storage_key=storage_key,
                content_type=IMAGE_CONTENT_TYPE,
                byte_size=byte_size,
            )
            await insert_job_image(session, job_id=job_id, position=position, asset_id=asset_id)
        succeeded = await transition_job_status(
            session,
            job_id,
            "succeeded",
            allowed_from=statuses_allowed_before("succeeded"),
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
