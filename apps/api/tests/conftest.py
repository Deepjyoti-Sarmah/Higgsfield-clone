# ruff: noqa: E402
# GENERATION_BACKEND must be set before app.settings is first instantiated, so the env write
# comes before the app imports below (settings is lru_cached on first call).
import os

os.environ.setdefault("GENERATION_BACKEND", "mock")

import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import create_database_engine, create_session_maker
from app.main import create_app
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage

API_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def migrate_database() -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API_DIR,
        check=True,
    )


@pytest.fixture
async def session_maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_database_engine(get_settings())
    yield create_session_maker(engine)
    await engine.dispose()


@pytest.fixture
def object_storage() -> InMemoryObjectStorage:
    return InMemoryObjectStorage()


@pytest.fixture
async def app(
    session_maker: async_sessionmaker[AsyncSession], object_storage: InMemoryObjectStorage
) -> AsyncIterator[FastAPI]:
    application = create_app()
    application.state.session_maker = session_maker
    application.dependency_overrides[get_object_storage] = lambda: object_storage
    yield application


def open_client(application: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=application), base_url="http://test")


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with open_client(app) as http_client:
        yield http_client


@pytest.fixture
async def guest_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with open_client(app) as http_client:
        signed_in = await http_client.post("/api/v1/auth/guest")
        assert signed_in.status_code == 201
        yield http_client


@pytest.fixture
async def other_guest_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with open_client(app) as http_client:
        signed_in = await http_client.post("/api/v1/auth/guest")
        assert signed_in.status_code == 201
        yield http_client


@pytest.fixture
async def client_without_database() -> AsyncIterator[AsyncClient]:
    unreachable = Settings(database_url="postgresql+asyncpg://postgres:postgres@127.0.0.1:1/none")
    engine = create_database_engine(unreachable)
    application = create_app()
    application.state.session_maker = create_session_maker(engine)
    async with open_client(application) as http_client:
        yield http_client
    await engine.dispose()
