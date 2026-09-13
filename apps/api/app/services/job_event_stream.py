import asyncio
import uuid
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.job_states import TERMINAL_STATUSES, JobStatus
from app.repositories.jobs import read_job_status
from app.schemas.jobs import JobStatusEvent
from app.services.job_event_broker import JobEventBroker

DEFAULT_PING_SECONDS = 20.0


async def stream_job_status_events(
    job_id: uuid.UUID,
    broker: JobEventBroker,
    session_maker: async_sessionmaker[AsyncSession],
    ping_seconds: float = DEFAULT_PING_SECONDS,
) -> AsyncIterator[str]:
    queue = broker.subscribe(job_id)
    try:
        yield "retry: 3000\n\n"
        status = await _read_status(session_maker, job_id)
        if status is None:
            return
        yield _status_frame(job_id, status)
        while status not in TERMINAL_STATUSES:
            if not await _wait_for_wake_up(queue, ping_seconds):
                yield ": ping\n\n"
                continue
            status = await _read_status(session_maker, job_id)
            if status is None:
                return
            yield _status_frame(job_id, status)
    finally:
        broker.unsubscribe(job_id, queue)


async def _read_status(
    session_maker: async_sessionmaker[AsyncSession], job_id: uuid.UUID
) -> JobStatus | None:
    async with session_maker() as session:
        status = await read_job_status(session, job_id)
    return None if status is None else _as_job_status(status)


async def _wait_for_wake_up(queue: asyncio.Queue[None], ping_seconds: float) -> bool:
    try:
        async with asyncio.timeout(ping_seconds):
            await queue.get()
    except TimeoutError:
        return False
    return True


def _status_frame(job_id: uuid.UUID, status: JobStatus) -> str:
    data = JobStatusEvent(job_id=job_id, status=status).model_dump_json()
    return f"event: status\ndata: {data}\n\n"


def _as_job_status(status: str) -> JobStatus:
    # The DB check constraint allows exactly these four values.
    return status  # type: ignore[return-value]
