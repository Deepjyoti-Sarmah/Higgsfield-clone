from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preset import Preset


async def list_active_presets(session: AsyncSession) -> list[Preset]:
    result = await session.execute(
        select(Preset).where(Preset.is_active.is_(True)).order_by(Preset.sort_order)
    )
    return list(result.scalars())


async def find_active_preset(session: AsyncSession, slug: str) -> Preset | None:
    result = await session.execute(
        select(Preset).where(Preset.slug == slug, Preset.is_active.is_(True))
    )
    return result.scalar_one_or_none()
