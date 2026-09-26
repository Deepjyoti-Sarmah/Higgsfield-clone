import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import hold_amount
from app.domain.sequence_rules import SEQUENCE_CREDIT_COST, STITCH_STEP_KIND
from app.models.job import Job
from app.repositories.assets import find_user_asset
from app.repositories.job_steps import insert_job_step
from app.repositories.jobs import find_job_by_idempotency_key, notify_job_event
from app.repositories.ledger import insert_ledger_entry, sum_user_balance
from app.repositories.sequence_jobs import (
    find_clip_source_jobs,
    insert_sequence_clips,
    insert_sequence_job,
    list_sequence_clips,
)
from app.repositories.users import lock_user_row
from app.schemas.sequence_jobs import SequenceClipIn
from app.services.image_job_creation import IdempotencyKeyConflictError
from app.services.job_creation import InsufficientCreditsError, enforce_creation_limits


@dataclass(frozen=True)
class SequenceJobCreation:
    id: uuid.UUID
    status: str
    credit_cost: int
    clip_count: int


class SequenceClipNotFoundError(Exception):
    """A clip id that isn't the caller's own job."""


class SequenceClipIneligibleError(Exception):
    def __init__(self, job_id: uuid.UUID, reason: str) -> None:
        super().__init__(f"clip {job_id} is ineligible: {reason}")
        self.job_id = job_id
        self.reason = reason


class AudioAssetNotFoundError(Exception):
    """The audio id isn't the caller's own ready input_audio asset."""


async def _replayed_creation(session: AsyncSession, job: Job) -> SequenceJobCreation:
    if job.kind != "sequence":
        raise IdempotencyKeyConflictError(str(job.id))
    clips = await list_sequence_clips(session, job.id)
    return SequenceJobCreation(
        id=job.id, status=job.status, credit_cost=job.credit_cost, clip_count=len(clips)
    )


def _check_clip_eligible(job_id: uuid.UUID, source: Job | None) -> None:
    if source is None:
        raise SequenceClipNotFoundError(str(job_id))
    if source.kind != "video":
        raise SequenceClipIneligibleError(job_id, "not a video job")
    if source.status != "succeeded":
        raise SequenceClipIneligibleError(job_id, "not succeeded")
    if source.output_video_asset_id is None:
        raise SequenceClipIneligibleError(job_id, "has no output video")


async def _check_audio_asset(
    session: AsyncSession, user_id: uuid.UUID, audio_asset_id: uuid.UUID | None
) -> uuid.UUID | None:
    if audio_asset_id is None:
        return None
    asset = await find_user_asset(session, user_id, audio_asset_id)
    if asset is None or asset.kind != "input_audio" or asset.status != "ready":
        raise AudioAssetNotFoundError(str(audio_asset_id))
    return asset.id


async def create_sequence_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    clips: list[SequenceClipIn],
    audio_asset_id: uuid.UUID | None,
    idempotency_key: str,
) -> SequenceJobCreation:
    await lock_user_row(session, user_id)
    existing = await find_job_by_idempotency_key(session, user_id, idempotency_key)
    if existing is not None:
        return await _replayed_creation(session, existing)
    await enforce_creation_limits(session, user_id, False, 0)
    sources = await find_clip_source_jobs(session, user_id, [clip.job_id for clip in clips])
    for clip in clips:
        _check_clip_eligible(clip.job_id, sources.get(clip.job_id))
    audio_id = await _check_audio_asset(session, user_id, audio_asset_id)
    balance = await sum_user_balance(session, user_id)
    if balance < SEQUENCE_CREDIT_COST:
        # rollback expires the loaded rows, so read the balance before releasing the lock
        await session.rollback()
        raise InsufficientCreditsError(balance=balance, required=SEQUENCE_CREDIT_COST)
    job = await insert_sequence_job(
        session,
        user_id=user_id,
        audio_asset_id=audio_id,
        idempotency_key=idempotency_key,
        credit_cost=SEQUENCE_CREDIT_COST,
    )
    await insert_sequence_clips(
        session,
        job.id,
        [(clip.job_id, clip.transition_in, clip.trim_start_ms, clip.trim_end_ms)
         for clip in clips],
    )
    await insert_job_step(session, job.id, STITCH_STEP_KIND)
    await insert_ledger_entry(
        session,
        user_id=user_id,
        kind="HOLD",
        amount=hold_amount(SEQUENCE_CREDIT_COST),
        job_id=job.id,
    )
    await notify_job_event(session, job.id)
    creation = SequenceJobCreation(
        id=job.id,
        status=job.status,
        credit_cost=job.credit_cost,
        clip_count=len(clips),
    )
    try:
        await session.commit()
    except IntegrityError:
        # A parallel create with the same key beat the lock: its row is the real one.
        await session.rollback()
        raced = await find_job_by_idempotency_key(session, user_id, idempotency_key)
        if raced is None:
            raise
        return await _replayed_creation(session, raced)
    return creation
