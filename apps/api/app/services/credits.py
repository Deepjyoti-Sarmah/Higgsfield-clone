import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import TOPUP_CREDITS
from app.repositories.ledger import insert_ledger_entry, sum_user_balance
from app.repositories.users import lock_user_row
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
