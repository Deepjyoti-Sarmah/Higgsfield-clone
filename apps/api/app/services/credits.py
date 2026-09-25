import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import TOPUP_CREDITS
from app.models.ledger_entry import LedgerEntry
from app.repositories.ledger import insert_ledger_entry, list_user_ledger_entries, sum_user_balance
from app.repositories.users import lock_user_row
from app.schemas.credits import LedgerEntryResponse, LedgerListResponse
from app.services import guardrails


@dataclass(frozen=True)
class TopUpResult:
    amount: int
    balance: int


async def read_balance(session: AsyncSession, user_id: uuid.UUID) -> int:
    return await sum_user_balance(session, user_id)


async def grant_top_up_credits(session: AsyncSession, user_id: uuid.UUID) -> TopUpResult:
    await lock_user_row(session, user_id)
    await guardrails.enforce_topup_limit(session, user_id)
    await insert_ledger_entry(session, user_id=user_id, kind="TOPUP", amount=TOPUP_CREDITS)
    balance = await read_balance(session, user_id)
    await session.commit()
    return TopUpResult(amount=TOPUP_CREDITS, balance=balance)


async def read_ledger(
    session: AsyncSession, user_id: uuid.UUID, limit: int
) -> LedgerListResponse:
    entries = await list_user_ledger_entries(session, user_id, limit)
    return LedgerListResponse(items=[_entry_response(entry) for entry in entries])


def _entry_response(entry: LedgerEntry) -> LedgerEntryResponse:
    return LedgerEntryResponse(
        id=entry.id,
        kind=entry.kind,  # type: ignore[arg-type]
        amount=entry.amount,
        job_id=entry.job_id,
        created_at=entry.created_at,
    )
