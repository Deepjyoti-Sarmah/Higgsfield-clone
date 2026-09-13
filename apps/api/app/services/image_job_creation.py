import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import hold_amount
from app.domain.image_rules import ImageQuality, image_credit_cost
from app.models.job import Job
from app.repositories.image_jobs import insert_image_job
from app.repositories.job_steps import insert_job_step
from app.repositories.jobs import find_job_by_idempotency_key, notify_job_event
from app.repositories.ledger import insert_ledger_entry, sum_user_balance
from app.repositories.users import lock_user_row
from app.services.job_creation import InsufficientCreditsError


@dataclass(frozen=True)
class ImageJobCreation:
    id: uuid.UUID
    status: str
    credit_cost: int
    image_count: int


class IdempotencyKeyConflictError(Exception):
    """The key already belongs to a job of another kind (video vs image)."""


def _replayed_creation(job: Job) -> ImageJobCreation:
    if job.kind != "image":
        raise IdempotencyKeyConflictError(str(job.id))
    return ImageJobCreation(
        id=job.id,
        status=job.status,
        credit_cost=job.credit_cost,
        image_count=job.image_count or 0,
    )


async def create_image_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    prompt: str,
    aspect_ratio: str,
    quality: ImageQuality,
    count: int,
    idempotency_key: str,
) -> ImageJobCreation:
    await lock_user_row(session, user_id)
    existing = await find_job_by_idempotency_key(session, user_id, idempotency_key)
    if existing is not None:
        return _replayed_creation(existing)
    required = image_credit_cost(quality, count)
    balance = await sum_user_balance(session, user_id)
    if balance < required:
        # rollback expires the loaded rows, so read the cost before releasing the lock
        await session.rollback()
        raise InsufficientCreditsError(balance=balance, required=required)
    job = await insert_image_job(
        session,
        user_id=user_id,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        quality=quality,
        image_count=count,
        idempotency_key=idempotency_key,
        credit_cost=required,
    )
    await insert_job_step(session, job.id, "generate_image")
    await insert_ledger_entry(
        session, user_id=user_id, kind="HOLD", amount=hold_amount(required), job_id=job.id
    )
    await notify_job_event(session, job.id)
    creation = ImageJobCreation(
        id=job.id, status=job.status, credit_cost=job.credit_cost, image_count=count
    )
    try:
        await session.commit()
    except IntegrityError:
        # A parallel create with the same key beat the lock: its row is the real one.
        await session.rollback()
        raced = await find_job_by_idempotency_key(session, user_id, idempotency_key)
        if raced is None:
            raise
        return _replayed_creation(raced)
    return creation
