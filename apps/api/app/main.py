from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import create_database_engine, create_session_maker
from app.logging_setup import configure_logging
from app.routers import (
    auth,
    credits,
    health,
    image_jobs,
    jobs,
    presets,
    share,
    share_page,
    uploads,
)
from app.services.job_event_broker import JobEventBroker
from app.settings import get_settings


@asynccontextmanager
async def open_database(app: FastAPI) -> AsyncIterator[None]:
    engine = create_database_engine(get_settings())
    app.state.session_maker = create_session_maker(engine)
    broker = JobEventBroker(engine)
    await broker.start()
    app.state.job_event_broker = broker
    try:
        yield
    finally:
        await broker.stop()
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
    configure_logging(get_settings().effective_log_format)
    app = FastAPI(title="Higgsfield Clone API", version="0.1.0", lifespan=open_database)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(presets.router)
    app.include_router(uploads.router)
    app.include_router(jobs.router)
    app.include_router(credits.router)
    app.include_router(image_jobs.router)
    app.include_router(share.router)
    # Before the SPA catch-all: Starlette matches in registration order, so /v/{job_id}
    # must be registered first or the catch-all would serve the bare shell without meta tags.
    app.include_router(share_page.router)
    mount_single_page_app(app, Path(get_settings().static_dir))
    return app


app = create_app()
