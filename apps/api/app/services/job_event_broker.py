import asyncio
import contextlib
import json
import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine

NOTIFY_CHANNEL = "job_events"
RECONNECT_DELAYS_SECONDS = (1, 2, 4, 8, 16, 30)
NotifyHandler = Callable[[object, int, str, str], None]
TerminationHandler = Callable[[object], None]


async def _add_notify_listener(
    listener: Any, on_notify: NotifyHandler, on_termination: TerminationHandler
) -> None:
    await listener.add_listener(NOTIFY_CHANNEL, on_notify)
    listener.add_termination_listener(on_termination)


class JobEventBroker:
    """ONE LISTEN connection per API process, fanning out to per-job wake-up queues."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._subscribers: dict[uuid.UUID, set[asyncio.Queue[None]]] = {}
        self._listener: Any = None
        self._connection: Any = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._is_stopped = False

    async def start(self) -> None:
        await self._open_listener_connection()

    async def stop(self) -> None:
        self._is_stopped = True
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
        self._reconnect_task = None
        self._terminate_listener()
        self._subscribers.clear()

    def subscribe(self, job_id: uuid.UUID) -> asyncio.Queue[None]:
        queue: asyncio.Queue[None] = asyncio.Queue(maxsize=1)
        self._subscribers.setdefault(job_id, set()).add(queue)
        return queue

    def unsubscribe(self, job_id: uuid.UUID, queue: asyncio.Queue[None]) -> None:
        queues = self._subscribers.get(job_id)
        if queues is None:
            return
        queues.discard(queue)
        if not queues:
            del self._subscribers[job_id]

    async def _open_listener_connection(self) -> None:
        connection = await self._engine.connect()
        try:
            raw = await connection.get_raw_connection()
            listener = raw.driver_connection
            await _add_notify_listener(listener, self._on_notify, self._on_termination)
        except Exception:
            self._release_connection(connection)
            await connection.close()
            raise
        self._listener = listener
        self._connection = connection

    def _on_notify(self, _connection: object, _pid: int, _channel: str, payload: str) -> None:
        job_id = parse_job_id(payload)
        if job_id is not None:
            self._wake(job_id)

    def _on_termination(self, _connection: object) -> None:
        if self._connection is None or self._is_stopped:
            return
        self._release_connection(self._connection)
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._reconnect())
    async def _reconnect(self) -> None:
        attempt = 0
        while True:
            delay = RECONNECT_DELAYS_SECONDS[min(attempt, len(RECONNECT_DELAYS_SECONDS) - 1)]
            attempt += 1
            await asyncio.sleep(delay)
            try:
                await self._open_listener_connection()
            except Exception:
                continue
            self._wake_all()
            return

    def _wake(self, job_id: uuid.UUID) -> None:
        for queue in list(self._subscribers.get(job_id, ())):
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(None)

    def _wake_all(self) -> None:
        for queues in list(self._subscribers.values()):
            for queue in list(queues):
                with contextlib.suppress(asyncio.QueueFull):
                    queue.put_nowait(None)

    def _release_connection(self, connection: Any) -> None:
        listener, self._listener = self._listener, None
        self._connection = None
        # asyncpg's terminate() is the public, synchronous abort that also fires the
        # termination listener, so a dead listener never lingers in SQLAlchemy's pool.
        if listener is not None:
            with contextlib.suppress(Exception):
                listener.terminate()
        if connection is not None:
            with contextlib.suppress(RuntimeError):
                asyncio.get_running_loop().create_task(connection.close())

    def _terminate_listener(self) -> None:
        self._release_connection(self._connection)


def parse_job_id(payload: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(json.loads(payload)["job_id"]))
    except (KeyError, TypeError, ValueError):
        return None
