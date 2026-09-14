import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlsplit

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.backend_selection import select_image_adapter, select_model_adapter
from app.adapters.object_storage import ObjectStorage
from app.settings import Settings

CheckStatus = Literal["ok", "degraded", "down"]

TCP_TIMEOUT_SECONDS = 5.0
SENTINEL_KEY = "health/deep-check"


async def is_database_reachable(session: AsyncSession) -> bool:
    try:
        await session.execute(text("select 1"))
    except (SQLAlchemyError, OSError):
        return False
    return True


@dataclass(frozen=True)
class CheckResult:
    status: CheckStatus
    duration_ms: int
    detail: str | dict[str, Any] | None = None


@dataclass(frozen=True)
class DeepHealth:
    status: CheckStatus
    duration_ms: int
    checks: dict[str, CheckResult] = field(default_factory=dict)


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


async def check_database(session: AsyncSession) -> CheckResult:
    started = time.monotonic()
    if await is_database_reachable(session):
        return CheckResult("ok", _elapsed_ms(started), None)
    return CheckResult("down", _elapsed_ms(started), "connect failed")


async def check_storage(storage: ObjectStorage) -> CheckResult:
    # A HEAD against a key that never exists still proves endpoint + credentials:
    # missing reads None, auth/network failures raise.
    started = time.monotonic()
    try:
        await storage.read_object_size(SENTINEL_KEY)
    except Exception as error:
        return CheckResult("down", _elapsed_ms(started), type(error).__name__)
    return CheckResult("ok", _elapsed_ms(started), "reachable")


async def _is_tcp_reachable(url: str) -> bool:
    parts = urlsplit(url)
    host = parts.hostname or ""
    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), TCP_TIMEOUT_SECONDS)
    except (OSError, TimeoutError, ValueError):
        return False
    writer.close()
    try:
        await writer.wait_closed()
    except (OSError, TimeoutError):
        pass
    return True


async def _check_configured_endpoint(name: str, endpoint_url: str) -> CheckResult:
    started = time.monotonic()
    if not endpoint_url:
        return CheckResult("down", _elapsed_ms(started), f"{name} endpoint not configured")
    if await _is_tcp_reachable(endpoint_url):
        return CheckResult("ok", _elapsed_ms(started), name)
    return CheckResult("down", _elapsed_ms(started), f"{name} endpoint unreachable")


async def check_video_backend(settings: Settings) -> CheckResult:
    name = select_model_adapter(settings).name
    if name in ("local-motion", "mock"):
        return CheckResult("ok", 0, name)
    if name == "modal":
        return await _check_configured_endpoint(name, settings.modal_endpoint_url)
    started = time.monotonic()
    if not settings.openrouter_api_key:
        return CheckResult("down", _elapsed_ms(started), "openrouter key not configured")
    if await _is_tcp_reachable("https://openrouter.ai"):
        return CheckResult("ok", _elapsed_ms(started), name)
    return CheckResult("down", _elapsed_ms(started), "openrouter unreachable")


async def check_image_backend(settings: Settings) -> CheckResult:
    name = select_image_adapter(settings).name
    if name != "modal":
        return CheckResult("ok", 0, name)
    return await _check_configured_endpoint(name, settings.modal_image_endpoint_url)


async def check_queue(session: AsyncSession) -> CheckResult:
    # Inline here because the brief scopes queue depth to this service; no repository owns it.
    started = time.monotonic()
    row = (
        await session.execute(
            text(
                "SELECT COUNT(*), EXTRACT(EPOCH FROM (now() - MIN(created_at)))"
                " FROM job_step WHERE status = 'queued'"
            )
        )
    ).one()
    depth, oldest = int(row[0]), row[1]
    return CheckResult("ok", _elapsed_ms(started), {
        "depth": depth,
        "oldest_age_seconds": None if oldest is None else round(float(oldest), 1),
    })


async def collect_deep_health(
    session: AsyncSession, storage: ObjectStorage, settings: Settings
) -> DeepHealth:
    started = time.monotonic()
    database = await check_database(session)
    storage_check = await check_storage(storage)
    video_backend = await check_video_backend(settings)
    image_backend = await check_image_backend(settings)
    queue = await check_queue(session)
    checks = {
        "database": database,
        "storage": storage_check,
        "video_backend": video_backend,
        "image_backend": image_backend,
        "queue": queue,
    }
    critical = (database, storage_check, video_backend, image_backend)
    status: CheckStatus = "down" if any(check.status == "down" for check in critical) else "ok"
    return DeepHealth(status, _elapsed_ms(started), checks)
