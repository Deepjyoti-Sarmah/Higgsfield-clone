import asyncio

from alembic import context
from sqlalchemy.engine import Connection

from app.db import Base, create_database_engine
from app.models import user  # noqa: F401  (registers the table on Base.metadata)
from app.settings import get_settings


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_database_engine(get_settings())
    async with engine.connect() as connection:
        await connection.run_sync(run_migrations)
        await connection.commit()
    await engine.dispose()


asyncio.run(run_migrations_online())
