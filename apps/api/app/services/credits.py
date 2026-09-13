import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.ledger import sum_user_balance


async def read_balance(session: AsyncSession, user_id: uuid.UUID) -> int:
    return await sum_user_balance(session, user_id)
