import asyncio
import logging
import os
import socket
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.backend_selection import (
    select_fallback_model_adapter,
    select_image_adapter,
    select_model_adapter,
)
from app.adapters.image_model_adapter import ImageModelAdapter
from app.adapters.model_adapter import ModelAdapter
from app.adapters.object_storage import ObjectStorage
from app.db import create_database_engine, create_session_maker
from app.repositories.job_steps import ClaimedStep
from app.services.generation_runs import RunSettings, run_claimed_step
from app.services.image_generation_runs import run_image_step
from app.services.lease_reaper import REAPER_BATCH_LIMIT, reap_expired_steps
from app.services.step_claiming import claim_step
from app.settings import get_settings
from app.storage_dependencies import get_object_storage

logger = logging.getLogger("worker")

IMAGE_STEP_KIND = "generate_image"


def build_worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


async def run_claimed_step_for_kind(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    storage: ObjectStorage,
    adapter: ModelAdapter,
    image_adapter: ImageModelAdapter,
    claimed: ClaimedStep,
    worker_id: str,
    settings: RunSettings,
    fallback_adapter: ModelAdapter | None = None,
) -> None:
    if claimed.kind == IMAGE_STEP_KIND:
        await run_image_step(
            session_maker,
            storage=storage,
            adapter=image_adapter,
            claimed=claimed,
            worker_id=worker_id,
            settings=settings,
        )
        return
    await run_claimed_step(
        session_maker,
        storage=storage,
        adapter=adapter,
        fallback_adapter=fallback_adapter,
        claimed=claimed,
        worker_id=worker_id,
        settings=settings,
    )


async def run_worker_loop() -> None:
    settings = get_settings()
    engine = create_database_engine(settings)
    session_maker = create_session_maker(engine)
    storage = get_object_storage()
    adapter = select_model_adapter(settings)
    fallback_adapter = select_fallback_model_adapter(settings)
    image_adapter = select_image_adapter(settings)
    run_settings = RunSettings(
        lease_seconds=settings.worker_lease_seconds,
        generation_timeout_seconds=settings.generation_timeout_seconds,
        download_url_ttl_seconds=settings.download_url_ttl_seconds,
        paid_budget_cents=settings.paid_budget_cents,
    )
    worker_id = build_worker_id()
    logger.info(
        "worker %s backend=%s image_backend=%s lease=%ss poll=%ss",
        worker_id,
        adapter.name,
        image_adapter.name,
        settings.worker_lease_seconds,
        settings.worker_poll_seconds,
    )
    last_reaped_at = 0.0
    try:
        while True:
            try:
                now = time.monotonic()
                if now - last_reaped_at >= settings.worker_reaper_seconds:
                    last_reaped_at = now
                    await reap_expired_steps(session_maker, limit=REAPER_BATCH_LIMIT)
                claimed = await claim_step(
                    session_maker, worker_id, settings.worker_lease_seconds
                )
                if claimed is None:
                    await asyncio.sleep(settings.worker_poll_seconds)
                    continue
                logger.info(
                    "claimed step %s job=%s attempt=%s", claimed.id, claimed.job_id, claimed.attempt
                )
                await run_claimed_step_for_kind(
                    session_maker,
                    storage=storage,
                    adapter=adapter,
                    image_adapter=image_adapter,
                    fallback_adapter=fallback_adapter,
                    claimed=claimed,
                    worker_id=worker_id,
                    settings=run_settings,
                )
                logger.info("finished step %s", claimed.id)
            except Exception:
                # A bad step or a dropped connection must never end the loop.
                logger.exception("worker loop error; retrying after the poll interval")
                await asyncio.sleep(settings.worker_poll_seconds)
    finally:
        await engine.dispose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    asyncio.run(run_worker_loop())


if __name__ == "__main__":
    main()
