import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import job, job_step, ledger_entry, preset, user  # noqa: F401 (FK registration)
from app.models.asset import Asset


async def insert_asset(
    session: AsyncSession,
    *,
    asset_id: uuid.UUID,
    user_id: uuid.UUID,
    kind: str,
    status: str,
    storage_key: str,
    content_type: str,
    byte_size: int | None = None,
) -> Asset:
    asset = Asset(
        id=asset_id,
        user_id=user_id,
        kind=kind,
        status=status,
        storage_key=storage_key,
        content_type=content_type,
        byte_size=byte_size,
    )
    session.add(asset)
    await session.flush()
    return asset


async def find_user_asset(
    session: AsyncSession, user_id: uuid.UUID, asset_id: uuid.UUID
) -> Asset | None:
    result = await session.execute(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def mark_asset_ready(session: AsyncSession, asset: Asset, byte_size: int) -> None:
    asset.status = "ready"
    asset.byte_size = byte_size
    asset.updated_at = datetime.now(UTC)
    await session.flush()


async def find_assets_by_ids(
    session: AsyncSession, ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, Asset]:
    if not ids:
        return {}
    result = await session.execute(select(Asset).where(Asset.id.in_(ids)))
    return {asset.id: asset for asset in result.scalars()}
