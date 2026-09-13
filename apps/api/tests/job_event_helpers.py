import asyncio
import contextlib
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.job_states import TERMINAL_STATUSES, statuses_allowed_before
from app.repositories.jobs import notify_job_event, transition_job_status
from app.services.job_event_broker import JobEventBroker
from app.services.job_event_stream import stream_job_status_events


@asynccontextmanager
async def open_broker(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[JobEventBroker]:
    broker = JobEventBroker(session_maker.kw["bind"])  # type: ignore[arg-type]
    await broker.start()
    try:
        yield broker
    finally:
        await broker.stop()


async def transition(
    session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID, to_status: str
) -> None:
    async with session_maker() as session:
        allowed_from = statuses_allowed_before(to_status)  # type: ignore[arg-type]
        changed = await transition_job_status(session, job_id, to_status, allowed_from=allowed_from)  # type: ignore[arg-type]
        assert changed
        await notify_job_event(session, job_id)
        await session.commit()


async def notify_only(session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID) -> None:
    async with session_maker() as session:
        await notify_job_event(session, job_id)
        await session.commit()


def status_of(chunk: str) -> str:
    return str(chunk.split('"status":"')[1].split('"')[0])


async def collect_events(
    job_id: uuid.UUID,
    broker: JobEventBroker,
    session_maker: async_sessionmaker[AsyncSession],
) -> tuple[list[str], list[float]]:
    stream = stream_job_status_events(job_id, broker, session_maker)
    frames: list[str] = []
    seen_at: list[float] = []
    started = time.monotonic()
    async for chunk in stream:
        if "data:" not in chunk:
            continue
        frames.append(chunk)
        seen_at.append(time.monotonic() - started)
        if status_of(chunk) in TERMINAL_STATUSES:
            break
    return frames, seen_at


async def drive_to_completion(
    session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID
) -> None:
    await asyncio.sleep(0.05)
    await transition(session_maker, job_id, "running")
    await asyncio.sleep(0.05)
    await transition(session_maker, job_id, "succeeded")


async def wait_for_wake_up(queue: asyncio.Queue[None], seconds: float = 2.0) -> bool:
    with contextlib.suppress(TimeoutError):
        async with asyncio.timeout(seconds):
            await queue.get()
        return True
    return False
