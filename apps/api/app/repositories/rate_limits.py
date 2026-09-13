import uuid
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_rules import PAID_BACKENDS
from app.models.guest_issuance import GuestIssuance
from app.models.job import Job
from app.models.ledger_entry import LedgerEntry


async def insert_guest_issuance(session: AsyncSession, ip_hash: str) -> None:
    session.add(GuestIssuance(ip_hash=ip_hash))
    await session.flush()


async def count_guests_for_ip_since(
    session: AsyncSession, ip_hash: str, since: datetime
) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(GuestIssuance)
        .where(GuestIssuance.ip_hash == ip_hash, GuestIssuance.created_at >= since)
    )
    return int(total or 0)


async def count_user_jobs_since(session: AsyncSession, user_id: uuid.UUID, since: datetime) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.user_id == user_id, Job.created_at >= since)
    )
    return int(total or 0)


async def count_user_ledger_since(
    session: AsyncSession, user_id: uuid.UUID, kind: str, since: datetime
) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(LedgerEntry)
        .where(
            LedgerEntry.user_id == user_id,
            LedgerEntry.kind == kind,
            LedgerEntry.created_at >= since,
        )
    )
    return int(total or 0)


async def sum_paid_spend_cents(
    session: AsyncSession, since: datetime, video_cents: int, image_cents: int
) -> int:
    spend = func.coalesce(
        func.sum(case((Job.kind == "video", video_cents), else_=image_cents)), 0
    )
    total = await session.scalar(
        select(spend).where(Job.generated_by.in_(PAID_BACKENDS), Job.created_at >= since)
    )
    return int(total or 0)
