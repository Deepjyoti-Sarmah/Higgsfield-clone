import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import hold_amount
from app.domain.faceswap_rules import FACESWAP_CREDIT_COST, FACESWAP_STEP_KIND
from app.models.asset import Asset
from app.models.job import Job
from app.repositories.assets import find_user_asset
from app.repositories.faceswap_jobs import insert_faceswap_job
from app.repositories.job_steps import insert_job_step
from app.repositories.jobs import find_job_by_idempotency_key, notify_job_event
from app.repositories.ledger import insert_ledger_entry, sum_user_balance
from app.repositories.users import lock_user_row
from app.services.image_job_creation import IdempotencyKeyConflictError
from app.services.job_creation import (
    INPUT_ASSET_KINDS,
    InsufficientCreditsError,
    enforce_creation_limits,
)


@dataclass(frozen=True)
class FaceSwapJobCreation:
    id: uuid.UUID
    status: str
    credit_cost: int


class FaceSwapAssetNotFoundError(Exception):
    """A source or target asset id isn't the caller's own ready input/output image."""


def _replayed_creation(job: Job) -> FaceSwapJobCreation:
    if job.kind != "faceswap":
        raise IdempotencyKeyConflictError(str(job.id))
    return FaceSwapJobCreation(id=job.id, status=job.status, credit_cost=job.credit_cost)


async def _find_eligible_asset(
    session: AsyncSession, user_id: uuid.UUID, asset_id: uuid.UUID
) -> Asset:
    asset = await find_user_asset(session, user_id, asset_id)
    if asset is None or asset.kind not in INPUT_ASSET_KINDS or asset.status != "ready":
        raise FaceSwapAssetNotFoundError(str(asset_id))
    return asset


async def create_faceswap_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    source_asset_id: uuid.UUID,
    target_asset_id: uuid.UUID,
    idempotency_key: str,
) -> FaceSwapJobCreation:
    await lock_user_row(session, user_id)
    existing = await find_job_by_idempotency_key(session, user_id, idempotency_key)
    if existing is not None:
        return _replayed_creation(existing)
    await enforce_creation_limits(session, user_id, False, 0)
    source = await _find_eligible_asset(session, user_id, source_asset_id)
    target = await _find_eligible_asset(session, user_id, target_asset_id)
    balance = await sum_user_balance(session, user_id)
    if balance < FACESWAP_CREDIT_COST:
        # rollback expires the loaded rows, so read the balance before releasing the lock
        await session.rollback()
        raise InsufficientCreditsError(balance=balance, required=FACESWAP_CREDIT_COST)
    job = await insert_faceswap_job(
        session,
        user_id=user_id,
        source_asset_id=source.id,
        target_asset_id=target.id,
        idempotency_key=idempotency_key,
        credit_cost=FACESWAP_CREDIT_COST,
    )
    await insert_job_step(session, job.id, FACESWAP_STEP_KIND)
    await insert_ledger_entry(
        session,
        user_id=user_id,
        kind="HOLD",
        amount=hold_amount(FACESWAP_CREDIT_COST),
        job_id=job.id,
    )
    await notify_job_event(session, job.id)
    creation = FaceSwapJobCreation(id=job.id, status=job.status, credit_cost=job.credit_cost)
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
