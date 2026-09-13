import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.credit_rules import (
    GUEST_PER_IP_DAILY,
    PAID_IMAGE_COST_CENTS,
    PAID_VIDEO_COST_CENTS,
    TOPUP_DAILY_LIMIT,
    USER_DAILY_JOBS,
)
from app.repositories import rate_limits

DAILY_JOB_WINDOW_HOURS = 24
UNKNOWN_IP = "unknown"


class GuestLimitError(Exception):
    def __init__(self, limit: int, used: int) -> None:
        super().__init__(f"guest limit reached ({used}/{limit})")
        self.limit = limit
        self.used = used


class DailyJobLimitError(Exception):
    def __init__(self, limit: int, used: int) -> None:
        super().__init__(f"daily job limit reached ({used}/{limit})")
        self.limit = limit
        self.used = used


class TopUpLimitError(Exception):
    def __init__(self, limit: int, used: int) -> None:
        super().__init__(f"daily top-up limit reached ({used}/{limit})")
        self.limit = limit
        self.used = used


class PaidBudgetExceededError(Exception):
    def __init__(self, spent_cents: int, budget_cents: int) -> None:
        super().__init__(f"paid budget exhausted ({spent_cents}/{budget_cents} cents)")
        self.spent_cents = spent_cents
        self.budget_cents = budget_cents


def utc_day_start(now: datetime | None = None) -> datetime:
    moment = now or datetime.now(UTC)
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


def utc_hours_ago(hours: int, now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) - timedelta(hours=hours)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or UNKNOWN_IP
    return request.client.host if request.client else UNKNOWN_IP


def hash_client_ip(ip: str, secret: str) -> str:
    return hashlib.sha256(f"{ip}{secret}".encode()).hexdigest()


async def enforce_guest_limit(session: AsyncSession, ip_hash: str) -> None:
    used = await rate_limits.count_guests_for_ip_since(session, ip_hash, utc_day_start())
    if used >= GUEST_PER_IP_DAILY:
        raise GuestLimitError(GUEST_PER_IP_DAILY, used)


async def enforce_daily_job_limit(session: AsyncSession, user_id: uuid.UUID) -> None:
    since = utc_hours_ago(DAILY_JOB_WINDOW_HOURS)
    used = await rate_limits.count_user_jobs_since(session, user_id, since)
    if used >= USER_DAILY_JOBS:
        raise DailyJobLimitError(USER_DAILY_JOBS, used)


async def enforce_topup_limit(session: AsyncSession, user_id: uuid.UUID) -> None:
    used = await rate_limits.count_user_ledger_since(session, user_id, "TOPUP", utc_day_start())
    if used >= TOPUP_DAILY_LIMIT:
        raise TopUpLimitError(TOPUP_DAILY_LIMIT, used)


async def paid_spend_cents(session: AsyncSession) -> int:
    return await rate_limits.sum_paid_spend_cents(
        session, utc_day_start(), PAID_VIDEO_COST_CENTS, PAID_IMAGE_COST_CENTS
    )


async def ensure_paid_budget(session: AsyncSession, budget_cents: int) -> None:
    spent = await paid_spend_cents(session)
    if spent >= budget_cents:
        raise PaidBudgetExceededError(spent, budget_cents)


async def is_paid_budget_exhausted(
    session_maker: async_sessionmaker[AsyncSession], budget_cents: int
) -> bool:
    async with session_maker() as session:
        return await paid_spend_cents(session) >= budget_cents
