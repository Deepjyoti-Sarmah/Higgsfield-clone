from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


async def is_database_reachable(session: AsyncSession) -> bool:
    try:
        await session.execute(text("select 1"))
    except (SQLAlchemyError, OSError):
        return False
    return True
