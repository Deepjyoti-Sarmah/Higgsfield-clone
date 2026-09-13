import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.mock_model_adapter import MockModelAdapter
from app.adapters.placeholder_image_adapter import (
    PlaceholderImageAdapter,
    UnconfiguredImageAdapter,
)
from app.repositories.job_steps import claim_next_queued_step
from app.services.generation_runs import RunSettings
from app.services.step_claiming import claim_step
from app.settings import Settings
from app.worker import run_claimed_step_for_kind
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import GUEST_GRANT, balance_of, create_queued_job, current_user_id

SessionMaker = async_sessionmaker[AsyncSession]
WORKER_ID = "image-test-worker"
DRAIN_WORKER = "image-drain-worker"
RUN_SETTINGS = RunSettings(
    lease_seconds=300, generation_timeout_seconds=30.0, download_url_ttl_seconds=900
)
STANDARD_TWO_IMAGES = 20


async def _drain_queued_steps(session_maker: SessionMaker) -> None:
    while True:
        async with session_maker() as session:
            claimed = await claim_next_queued_step(session, DRAIN_WORKER, 300)
            await session.commit()
        if claimed is None:
            return


async def _create_image_job(guest_client: AsyncClient, key: str, count: int) -> uuid.UUID:
    body: dict[str, object] = {"prompt": "a cat", "aspect_ratio": "1:1", "quality": "standard"}
    body.update(count=count, idempotency_key=key)
    response = await guest_client.post("/api/v1/image-jobs", json=body)
    assert response.status_code == 202
    return uuid.UUID(response.json()["id"])


async def _run_step(
    session_maker: SessionMaker,
    storage: InMemoryObjectStorage,
    video_adapter: object,
    image_adapter: object,
    job_id: uuid.UUID,
) -> None:
    claimed = await claim_step(session_maker, WORKER_ID, RUN_SETTINGS.lease_seconds)
    assert claimed is not None and claimed.job_id == job_id
    await run_claimed_step_for_kind(
        session_maker,
        storage=storage,
        adapter=video_adapter,  # type: ignore[arg-type]
        image_adapter=image_adapter,  # type: ignore[arg-type]
        claimed=claimed,
        worker_id=WORKER_ID,
        settings=RUN_SETTINGS,
    )


async def test_a_claimed_image_step_stores_outputs_and_settles(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    await _drain_queued_steps(session_maker)
    user_id = uuid.UUID(await current_user_id(guest_client))
    job_id = await _create_image_job(guest_client, "t009-step-ok-1", count=2)

    await _run_step(
        session_maker,
        object_storage,
        MockModelAdapter(Settings()),
        PlaceholderImageAdapter("local-motion"),
        job_id,
    )

    body = (await guest_client.get(f"/api/v1/image-jobs/{job_id}")).json()
    assert body["status"] == "succeeded"
    assert body["backend"] == "local-motion"
    assert [url.split("/")[-1] for url in body["image_urls"]] == [
        "image-1.png?get",
        "image-2.png?get",
    ]
    async with session_maker() as session:
        kinds = dict(
            (
                await session.execute(
                    text("SELECT kind, count(*) FROM asset WHERE user_id = :u GROUP BY kind"),
                    {"u": user_id},
                )
            ).all()
        )
        positions = list(
            (
                await session.execute(
                    text("SELECT position FROM job_image WHERE job_id = :j ORDER BY position"),
                    {"j": job_id},
                )
            ).scalars()
        )
        output_fks = (
            await session.execute(
                text("SELECT output_video_asset_id, output_poster_asset_id FROM job WHERE id = :j"),
                {"j": job_id},
            )
        ).one()
    assert kinds == {"output_image": 2}
    assert positions == [1, 2]
    assert tuple(output_fks) == (None, None)
    assert await balance_of(guest_client) == GUEST_GRANT - STANDARD_TWO_IMAGES


async def test_an_unconfigured_image_backend_fails_and_refunds(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    await _drain_queued_steps(session_maker)
    user_id = uuid.UUID(await current_user_id(guest_client))
    job_id = await _create_image_job(guest_client, "t009-step-fail-1", count=1)

    await _run_step(
        session_maker,
        object_storage,
        MockModelAdapter(Settings()),
        UnconfiguredImageAdapter("modal"),
        job_id,
    )

    body = (await guest_client.get(f"/api/v1/image-jobs/{job_id}")).json()
    assert body["status"] == "failed"
    assert "not configured" in body["error_message"]
    assert await balance_of(guest_client) == GUEST_GRANT
    async with session_maker() as session:
        backend = await session.scalar(
            text("SELECT backend FROM job_step WHERE job_id = :j"), {"j": job_id}
        )
        released = await session.scalar(
            text("SELECT count(*) FROM ledger_entry WHERE job_id = :j AND kind = 'RELEASE'"),
            {"j": job_id},
        )
        images = await session.scalar(
            text("SELECT count(*) FROM job_image WHERE job_id = :j"), {"j": job_id}
        )
        assets = await session.scalar(
            text("SELECT count(*) FROM asset WHERE user_id = :u"), {"u": user_id}
        )
    assert (backend, released, images, assets) == ("modal", 1, 0, 0)


async def test_the_video_step_path_is_unchanged(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    await _drain_queued_steps(session_maker)
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "t009-step-video-1"))

    await _run_step(
        session_maker,
        object_storage,
        MockModelAdapter(Settings()),
        PlaceholderImageAdapter("local-motion"),
        job_id,
    )

    body = (await guest_client.get(f"/api/v1/jobs/{job_id}")).json()
    assert body["status"] == "succeeded"
    assert body["video_url"] is not None
    assert body["poster_url"] is not None


async def test_an_unknown_step_kind_creates_nothing(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage, session_maker: SessionMaker
) -> None:
    await _drain_queued_steps(session_maker)
    user_id = uuid.UUID(await current_user_id(guest_client))
    job_id = await _create_image_job(guest_client, "t009-step-odd-1", count=1)
    async with session_maker() as session:
        await session.execute(
            text("UPDATE job_step SET kind = 'generate_unknown' WHERE job_id = :j"), {"j": job_id}
        )
        await session.commit()

    await _run_step(
        session_maker,
        object_storage,
        MockModelAdapter(Settings()),
        PlaceholderImageAdapter("local-motion"),
        job_id,
    )

    async with session_maker() as session:
        assets = await session.scalar(
            text("SELECT count(*) FROM asset WHERE user_id = :u"), {"u": user_id}
        )
    assert assets == 0
