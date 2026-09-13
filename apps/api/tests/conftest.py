from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import Base, create_database_engine, create_session_maker
from app.main import create_app
from app.settings import Settings, get_settings


async def open_client(settings: Settings, is_schema_needed: bool) -> AsyncIterator[AsyncClient]:
    engine = create_database_engine(settings)
    if is_schema_needed:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    app = create_app()
    app.state.session_maker = create_session_maker(engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async for http_client in open_client(get_settings(), is_schema_needed=True):
        yield http_client


@pytest.fixture
async def client_without_database() -> AsyncIterator[AsyncClient]:
    unreachable = Settings(database_url="postgresql+asyncpg://postgres:postgres@127.0.0.1:1/none")
    async for http_client in open_client(unreachable, is_schema_needed=False):
        yield http_client
