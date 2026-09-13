from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import create_database_engine, create_session_maker
from app.routers import auth, health
from app.settings import get_settings


@asynccontextmanager
async def open_database(app: FastAPI) -> AsyncIterator[None]:
    engine = create_database_engine(get_settings())
    app.state.session_maker = create_session_maker(engine)
    yield
    await engine.dispose()


def mount_single_page_app(app: FastAPI, static_dir: Path) -> None:
    if not (static_dir / "index.html").is_file():
        return
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_single_page_app(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        candidate = (static_dir / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(static_dir.resolve()):
            return FileResponse(candidate)
        return FileResponse(static_dir / "index.html")


def create_app() -> FastAPI:
    app = FastAPI(title="Higgsfield Clone API", version="0.1.0", lifespan=open_database)
    app.include_router(health.router)
    app.include_router(auth.router)
    mount_single_page_app(app, Path(get_settings().static_dir))
    return app


app = create_app()
