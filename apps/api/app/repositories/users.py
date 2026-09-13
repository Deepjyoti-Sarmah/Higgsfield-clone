import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AppUser


async def insert_guest_user(session: AsyncSession) -> AppUser:
    user = AppUser(is_guest=True)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def find_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> AppUser | None:
    return await session.get(AppUser, user_id)


async def lock_user_row(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(select(AppUser.id).where(AppUser.id == user_id).with_for_update())
