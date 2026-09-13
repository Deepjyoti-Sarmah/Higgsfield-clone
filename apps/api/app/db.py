from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.settings import Settings


class Base(DeclarativeBase):
    pass


def create_database_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.async_database_url, pool_pre_ping=True)


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_maker: async_sessionmaker[AsyncSession] = request.app.state.session_maker
    async with session_maker() as session:
        yield session
