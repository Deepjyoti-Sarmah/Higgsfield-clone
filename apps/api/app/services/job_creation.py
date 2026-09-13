import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import hold_amount
from app.repositories.assets import find_user_asset
from app.repositories.job_steps import insert_job_step
from app.repositories.jobs import find_job_by_idempotency_key, insert_job, notify_job_event
from app.repositories.ledger import insert_ledger_entry, sum_user_balance
from app.repositories.presets import find_active_preset
from app.repositories.users import lock_user_row
from app.services import guardrails


class PresetNotFoundError(Exception):
    """No active preset with the requested slug."""


class InputAssetNotFoundError(Exception):
    """The input image does not exist or belongs to another user."""


class InputAssetNotReadyError(Exception):
    """The presigned upload of the input image has not completed yet."""


@dataclass(frozen=True)
class JobCreation:
    id: uuid.UUID
    status: str
    credit_cost: int


class InsufficientCreditsError(Exception):
    def __init__(self, balance: int, required: int) -> None:
        super().__init__(f"balance={balance} required={required}")
        self.balance = balance
        self.required = required


async def enforce_creation_limits(
    session: AsyncSession,
    user_id: uuid.UUID,
    is_paid_backend: bool,
    paid_budget_cents: int,
) -> None:
    await guardrails.enforce_daily_job_limit(session, user_id)
    if is_paid_backend:
        await guardrails.ensure_paid_budget(session, paid_budget_cents)


async def create_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    preset_slug: str,
    input_asset_id: uuid.UUID,
    prompt: str | None,
    idempotency_key: str,
    is_paid_backend: bool = False,
    paid_budget_cents: int = 0,
) -> JobCreation:
    await lock_user_row(session, user_id)
    existing = await find_job_by_idempotency_key(session, user_id, idempotency_key)
    if existing is not None:
        return JobCreation(id=existing.id, status=existing.status, credit_cost=existing.credit_cost)
    preset = await find_active_preset(session, preset_slug)
    if preset is None:
        raise PresetNotFoundError(preset_slug)
    asset = await find_user_asset(session, user_id, input_asset_id)
    if asset is None or asset.kind != "input_image":
        raise InputAssetNotFoundError(str(input_asset_id))
    if asset.status != "ready":
        raise InputAssetNotReadyError(str(input_asset_id))
    await enforce_creation_limits(session, user_id, is_paid_backend, paid_budget_cents)
    balance = await sum_user_balance(session, user_id)
    required = preset.credit_cost
    if balance < required:
        # rollback expires the loaded rows, so read the cost before releasing the lock
        await session.rollback()
        raise InsufficientCreditsError(balance=balance, required=required)
    job = await insert_job(
        session,
        user_id=user_id,
        preset_slug=preset.slug,
        input_asset_id=input_asset_id,
        prompt=prompt,
        idempotency_key=idempotency_key,
        credit_cost=preset.credit_cost,
    )
    await insert_job_step(session, job.id, "generate_video")
    await insert_ledger_entry(
        session, user_id=user_id, kind="HOLD", amount=hold_amount(job.credit_cost), job_id=job.id
    )
    await notify_job_event(session, job.id)
    creation = JobCreation(id=job.id, status=job.status, credit_cost=job.credit_cost)
    try:
        await session.commit()
    except IntegrityError:
        # A parallel create with the same key beat the lock: its row is the real one.
        await session.rollback()
        raced = await find_job_by_idempotency_key(session, user_id, idempotency_key)
        if raced is None:
            raise
        return JobCreation(id=raced.id, status=raced.status, credit_cost=raced.credit_cost)
    return creation
