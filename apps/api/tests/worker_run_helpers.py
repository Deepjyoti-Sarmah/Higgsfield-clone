import uuid
from pathlib import Path

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.model_adapter import GenerationRequest, GenerationResult
from app.repositories.job_steps import ClaimedStep, claim_next_queued_step
from app.services.adapter_runs import RunSettings
from app.services.generation_runs import run_claimed_step
from app.services.step_claiming import claim_step
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import create_ready_asset, current_user_id, post_job

LEASE_SECONDS = 300
WORKER_ID = "guardrails-worker"
DRAIN_WORKER = "guardrails-drain"
RUN_SETTINGS = RunSettings(
    lease_seconds=300,
    generation_timeout_seconds=60,
    download_url_ttl_seconds=3600,
    paid_budget_cents=500,
)
REAL_PREVIEW_JPEG = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "adapters"
    / "fixtures"
    / "preview_sources"
    / "source-01.jpg"
)


class RecordingAdapter:
    """A paid backend that must never be reached while the budget is exhausted."""

    name = "modal"

    def __init__(self) -> None:
        self.calls = 0

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        self.calls += 1
        raise AssertionError("the paid adapter must not be called")


async def drain_steps(session_maker: async_sessionmaker[AsyncSession]) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, LEASE_SECONDS)
            await session.commit()
        if claimed is None:
            return


async def create_and_claim(
    guest_client: AsyncClient,
    storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
    key: str,
) -> tuple[uuid.UUID, ClaimedStep]:
    await drain_steps(session_maker)
    user_id = await current_user_id(guest_client)
    asset = await create_ready_asset(guest_client, storage)
    storage.put_bytes(
        f"users/{user_id}/inputs/{asset['asset_id']}.jpg", REAL_PREVIEW_JPEG.read_bytes()
    )
    created = await post_job(guest_client, asset["asset_id"], key)
    assert created.status_code == 202, created.text
    job_id = uuid.UUID(created.json()["id"])
    claimed = await claim_step(session_maker, WORKER_ID, LEASE_SECONDS)
    assert claimed is not None and claimed.job_id == job_id
    return job_id, claimed


async def run_video_step(
    session_maker: async_sessionmaker[AsyncSession],
    storage: InMemoryObjectStorage,
    claimed: ClaimedStep,
    adapter: object,
    *,
    fallback: object | None = None,
    settings: RunSettings = RUN_SETTINGS,
) -> None:
    await run_claimed_step(
        session_maker,
        storage=storage,
        adapter=adapter,  # type: ignore[arg-type]
        fallback_adapter=fallback,  # type: ignore[arg-type]
        claimed=claimed,
        worker_id=WORKER_ID,
        settings=settings,
    )
