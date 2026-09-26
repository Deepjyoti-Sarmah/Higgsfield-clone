import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import hold_amount
from app.domain.video_faceswap_rules import (
    VIDEO_FACESWAP_MAX_BYTES,
    VIDEO_FACESWAP_MAX_SECONDS,
    VIDEO_FACESWAP_STEP_KIND,
    VIDEO_FACESWAP_TARGET_CONTENT_TYPE,
    video_faceswap_cost,
)
from app.models.asset import Asset
from app.models.job import Job
from app.repositories.assets import find_user_asset
from app.repositories.job_steps import insert_job_step
from app.repositories.jobs import find_job_by_idempotency_key, notify_job_event
from app.repositories.ledger import insert_ledger_entry, sum_user_balance
from app.repositories.users import lock_user_row
from app.repositories.video_faceswap_jobs import (
    find_owned_target_job,
    find_owned_video_producer,
    insert_video_faceswap_job,
)
from app.services.image_job_creation import IdempotencyKeyConflictError
from app.services.job_creation import (
    INPUT_ASSET_KINDS,
    InsufficientCreditsError,
    enforce_creation_limits,
)


@dataclass(frozen=True)
class VideoFaceSwapJobCreation:
    id: uuid.UUID
    status: str
    credit_cost: int


class VideoFaceSwapSourceNotFoundError(Exception):
    """The source photo id isn't the caller's own ready input/output image."""


class VideoFaceSwapTargetNotFoundError(Exception):
    """The target video id isn't the caller's own asset."""


class VideoFaceSwapTargetInvalidError(Exception):
    """The target is owned but not an eligible mp4 within the duration/size limits."""


class VideoFaceSwapKeyframeNotFoundError(Exception):
    """The keyframe preview id isn't the caller's own asset."""


def _replayed_creation(job: Job) -> VideoFaceSwapJobCreation:
    if job.kind != "video_faceswap":
        raise IdempotencyKeyConflictError(str(job.id))
    return VideoFaceSwapJobCreation(id=job.id, status=job.status, credit_cost=job.credit_cost)


async def _find_source(
    session: AsyncSession, user_id: uuid.UUID, asset_id: uuid.UUID
) -> Asset:
    asset = await find_user_asset(session, user_id, asset_id)
    if asset is None or asset.kind not in INPUT_ASSET_KINDS or asset.status != "ready":
        raise VideoFaceSwapSourceNotFoundError(str(asset_id))
    return asset


async def _find_target(
    session: AsyncSession, user_id: uuid.UUID, asset_id: uuid.UUID
) -> Asset:
    asset = await find_user_asset(session, user_id, asset_id)
    if asset is None:
        raise VideoFaceSwapTargetNotFoundError(str(asset_id))
    if asset.kind != "output_video" or asset.status != "ready":
        raise VideoFaceSwapTargetInvalidError(f"not a ready output video: {asset_id}")
    if asset.content_type != VIDEO_FACESWAP_TARGET_CONTENT_TYPE:
        raise VideoFaceSwapTargetInvalidError(f"target must be mp4: {asset_id}")
    if asset.byte_size is None or asset.byte_size > VIDEO_FACESWAP_MAX_BYTES:
        raise VideoFaceSwapTargetInvalidError(f"target over size limit: {asset_id}")
    return asset


async def _target_duration_ms(
    session: AsyncSession, user_id: uuid.UUID, target: Asset
) -> int:
    producer = await find_owned_video_producer(session, user_id, target.id)
    duration_ms = None if producer is None else producer.duration_ms
    if duration_ms is None or duration_ms <= 0:
        raise VideoFaceSwapTargetInvalidError(f"target duration unknown: {target.id}")
    if duration_ms > VIDEO_FACESWAP_MAX_SECONDS * 1000:
        raise VideoFaceSwapTargetInvalidError(f"target over duration limit: {target.id}")
    return duration_ms


async def _resolve_target(
    session: AsyncSession,
    user_id: uuid.UUID,
    target_asset_id: uuid.UUID | None,
    target_job_id: uuid.UUID | None,
) -> Asset:
    if target_job_id is None:
        assert target_asset_id is not None
        return await _find_target(session, user_id, target_asset_id)
    job = await find_owned_target_job(session, user_id, target_job_id)
    if job is None:
        raise VideoFaceSwapTargetNotFoundError(str(target_job_id))
    if job.kind not in ("video", "sequence"):
        raise VideoFaceSwapTargetInvalidError(f"job is not a video target: {target_job_id}")
    if job.status != "succeeded" or job.output_video_asset_id is None:
        raise VideoFaceSwapTargetInvalidError(f"job has no ready output video: {target_job_id}")
    return await _find_target(session, user_id, job.output_video_asset_id)


async def _check_keyframe(
    session: AsyncSession, user_id: uuid.UUID, keyframe_asset_id: uuid.UUID | None
) -> None:
    if keyframe_asset_id is None:
        return
    if await find_user_asset(session, user_id, keyframe_asset_id) is None:
        raise VideoFaceSwapKeyframeNotFoundError(str(keyframe_asset_id))


async def create_video_faceswap_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    source_asset_id: uuid.UUID,
    target_asset_id: uuid.UUID | None,
    target_job_id: uuid.UUID | None,
    keyframe_asset_id: uuid.UUID | None,
    idempotency_key: str,
) -> VideoFaceSwapJobCreation:
    await lock_user_row(session, user_id)
    existing = await find_job_by_idempotency_key(session, user_id, idempotency_key)
    if existing is not None:
        return _replayed_creation(existing)
    await enforce_creation_limits(session, user_id, False, 0)
    source = await _find_source(session, user_id, source_asset_id)
    target = await _resolve_target(session, user_id, target_asset_id, target_job_id)
    await _check_keyframe(session, user_id, keyframe_asset_id)
    duration_ms = await _target_duration_ms(session, user_id, target)
    cost = video_faceswap_cost(duration_ms)
    balance = await sum_user_balance(session, user_id)
    if balance < cost:
        # rollback expires the loaded rows, so read the balance before releasing the lock
        await session.rollback()
        raise InsufficientCreditsError(balance=balance, required=cost)
    job = await insert_video_faceswap_job(
        session,
        user_id=user_id,
        source_asset_id=source.id,
        target_asset_id=target.id,
        idempotency_key=idempotency_key,
        credit_cost=cost,
        duration_ms=duration_ms,
    )
    await insert_job_step(session, job.id, VIDEO_FACESWAP_STEP_KIND)
    await insert_ledger_entry(
        session,
        user_id=user_id,
        kind="HOLD",
        amount=hold_amount(cost),
        job_id=job.id,
    )
    await notify_job_event(session, job.id)
    creation = VideoFaceSwapJobCreation(id=job.id, status=job.status, credit_cost=job.credit_cost)
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
