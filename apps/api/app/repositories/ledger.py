import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import LedgerKind
from app.models import asset, job, job_step, preset, user  # noqa: F401 (FK registration)
from app.models.ledger_entry import LedgerEntry


async def insert_ledger_entry(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    kind: LedgerKind,
    amount: int,
    job_id: uuid.UUID | None = None,
) -> LedgerEntry:
    entry = LedgerEntry(user_id=user_id, kind=kind, amount=amount, job_id=job_id)
    session.add(entry)
    await session.flush()
    return entry


async def sum_user_balance(session: AsyncSession, user_id: uuid.UUID) -> int:
    total = await session.scalar(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(LedgerEntry.user_id == user_id)
    )
    return int(total or 0)
