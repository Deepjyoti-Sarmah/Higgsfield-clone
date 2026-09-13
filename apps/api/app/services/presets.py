from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preset import Preset
from app.repositories.presets import list_active_presets


async def read_presets(session: AsyncSession) -> list[Preset]:
    return await list_active_presets(session)
