import asyncio
import logging
import os
import socket
import time
import uuid

from app.adapters.backend_selection import select_model_adapter
from app.db import create_database_engine, create_session_maker
from app.services.generation_runs import RunSettings, run_claimed_step
from app.services.lease_reaper import REAPER_BATCH_LIMIT, reap_expired_steps
from app.services.step_claiming import claim_step
from app.settings import get_settings
from app.storage_dependencies import get_object_storage

logger = logging.getLogger("worker")


def build_worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


async def run_worker_loop() -> None:
    settings = get_settings()
    engine = create_database_engine(settings)
    session_maker = create_session_maker(engine)
    storage = get_object_storage()
    adapter = select_model_adapter(settings)
    run_settings = RunSettings(
        lease_seconds=settings.worker_lease_seconds,
        generation_timeout_seconds=settings.generation_timeout_seconds,
        download_url_ttl_seconds=settings.download_url_ttl_seconds,
    )
    worker_id = build_worker_id()
    logger.info(
        "worker %s backend=%s lease=%ss poll=%ss",
        worker_id,
        adapter.name,
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
                await run_claimed_step(
                    session_maker,
                    storage=storage,
                    adapter=adapter,
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
