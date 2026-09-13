import asyncio
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.model_adapter import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    ModelAdapter,
)
from app.adapters.object_storage import ObjectStorage
from app.repositories.job_steps import ClaimedStep, renew_step_lease
from app.services.guardrails import is_paid_budget_exhausted
from app.services.step_inputs import StepInputs

logger = logging.getLogger(__name__)

LEASE_RENEWALS_PER_LEASE = 5


@dataclass(frozen=True)
class RunSettings:
    lease_seconds: int
    generation_timeout_seconds: float
    download_url_ttl_seconds: int
    paid_budget_cents: int = 0


async def run_adapter_with_lease(
    session_maker: async_sessionmaker[AsyncSession],
    storage: ObjectStorage,
    adapter: ModelAdapter,
    claimed: ClaimedStep,
    inputs: StepInputs,
    worker_id: str,
    work_dir: Path,
    settings: RunSettings,
) -> GenerationResult | None:
    input_path = work_dir / "input"
    await storage.download_to_path(inputs.input_key, input_path)
    request = GenerationRequest(
        job_id=claimed.job_id,
        preset_slug=inputs.preset_slug,
        prompt=inputs.prompt,
        input_image_path=input_path,
        input_image_url=storage.create_download_url(
            inputs.input_key, settings.download_url_ttl_seconds
        ),
        work_dir=work_dir,
    )
    adapter_task = asyncio.create_task(
        asyncio.wait_for(adapter.generate_video(request), settings.generation_timeout_seconds)
    )
    renewal_task = asyncio.create_task(
        renew_lease_until_lost(session_maker, claimed.id, worker_id, settings.lease_seconds)
    )
    try:
        done, _ = await asyncio.wait({adapter_task, renewal_task}, return_when=asyncio.FIRST_COMPLETED)
        if renewal_task in done:
            logger.warning("lease lost for step %s; discarding the run", claimed.id)
            return None
        return adapter_task.result()
    finally:
        adapter_task.cancel()
        renewal_task.cancel()
        await asyncio.gather(adapter_task, renewal_task, return_exceptions=True)


async def run_adapter_with_fallback(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    storage: ObjectStorage,
    primary: ModelAdapter,
    fallback: ModelAdapter | None,
    claimed: ClaimedStep,
    inputs: StepInputs,
    worker_id: str,
    work_dir: Path,
    settings: RunSettings,
) -> tuple[GenerationResult, str] | None:
    selected = primary
    if fallback is not None and await is_paid_budget_exhausted(
        session_maker, settings.paid_budget_cents
    ):
        logger.warning("paid budget exhausted; using %s for step %s", fallback.name, claimed.id)
        selected = fallback
    try:
        result = await run_adapter_with_lease(
            session_maker, storage, selected, claimed, inputs, worker_id, work_dir, settings
        )
        return None if result is None else (result, selected.name)
    except (GenerationError, TimeoutError) as error:
        if fallback is None or selected is fallback:
            raise
        logger.warning(
            "backend %s failed for step %s (%s); falling back to %s",
            selected.name,
            claimed.id,
            error,
            fallback.name,
        )
    result = await run_adapter_with_lease(
        session_maker, storage, fallback, claimed, inputs, worker_id, work_dir, settings
    )
    return None if result is None else (result, fallback.name)


async def renew_lease_until_lost(
    session_maker: async_sessionmaker[AsyncSession],
    step_id: uuid.UUID,
    worker_id: str,
    lease_seconds: int,
) -> bool:
    interval_seconds = lease_seconds / LEASE_RENEWALS_PER_LEASE
    while True:
        await asyncio.sleep(interval_seconds)
        async with session_maker() as session:
            renewed = await renew_step_lease(session, step_id, worker_id, lease_seconds)
            if renewed:
                await session.commit()
        if not renewed:
            return True
