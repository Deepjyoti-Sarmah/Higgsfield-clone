import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import GUEST_GRANT_CREDITS
from app.models.user import AppUser
from app.repositories import rate_limits
from app.repositories.ledger import insert_ledger_entry
from app.repositories.users import find_user_by_id, insert_guest_user
from app.services import guardrails


async def create_guest_account(session: AsyncSession, *, ip_hash: str) -> AppUser:
    await guardrails.enforce_guest_limit(session, ip_hash)
    user = await insert_guest_user(session)
    await insert_ledger_entry(session, user_id=user.id, kind="GRANT", amount=GUEST_GRANT_CREDITS)
    await rate_limits.insert_guest_issuance(session, ip_hash)
    await session.commit()
    return user


async def find_account(session: AsyncSession, user_id: uuid.UUID) -> AppUser | None:
    return await find_user_by_id(session, user_id)
