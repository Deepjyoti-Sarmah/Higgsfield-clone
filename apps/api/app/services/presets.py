from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage, build_asset_url
from app.domain.preset_catalog import PREVIEW_KEYS
from app.models.preset import Preset
from app.repositories.presets import list_active_presets
from app.settings import Settings


async def read_presets(
    session: AsyncSession, storage: ObjectStorage, settings: Settings
) -> list[Preset]:
    presets = await list_active_presets(session)
    for preset in presets:
        if preset.preview_key is None:
            preset.preview_key = PREVIEW_KEYS.get(preset.slug)
    return presets


def preview_url_for(
    preset: Preset, storage: ObjectStorage, settings: Settings
) -> str | None:
    if preset.preview_key is None:
        return None
    return build_asset_url(
        storage,
        preset.preview_key,
        settings.s3_public_base_url,
        settings.download_url_ttl_seconds,
    )
