import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage, build_asset_url
from app.models.asset import Asset
from app.models.job import Job
from app.repositories.assets import find_assets_by_ids
from app.repositories.jobs import find_job
from app.repositories.presets import find_active_preset
from app.settings import Settings


@dataclass(frozen=True)
class PublicJobView:
    job: Job
    preset_name: str
    poster_url: str | None
    video_url: str | None


async def read_public_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    job_id: uuid.UUID,
) -> PublicJobView | None:
    job = await find_job(session, job_id)
    # The public share page is video-only (spec 007); an image job id answers 404.
    if job is None or job.preset_slug is None:
        return None
    preset = await find_active_preset(session, job.preset_slug)
    asset_ids = [
        asset_id
        for asset_id in (job.output_video_asset_id, job.output_poster_asset_id)
        if asset_id is not None
    ]
    assets = await find_assets_by_ids(session, asset_ids)
    return PublicJobView(
        job=job,
        preset_name=job.preset_slug if preset is None else preset.name,
        poster_url=_asset_url(storage, settings, assets, job.output_poster_asset_id),
        video_url=_asset_url(storage, settings, assets, job.output_video_asset_id),
    )


# Mirrors services/job_views.py: only a `ready` asset gets a URL, never a pending one.
def _asset_url(
    storage: ObjectStorage,
    settings: Settings,
    assets: dict[uuid.UUID, Asset],
    asset_id: uuid.UUID | None,
) -> str | None:
    return None if asset_id is None else _ready_url(storage, settings, assets.get(asset_id))


def _ready_url(storage: ObjectStorage, settings: Settings, asset: Asset | None) -> str | None:
    if asset is None or asset.status != "ready":
        return None
    return build_asset_url(
        storage, asset.storage_key, settings.s3_public_base_url, settings.download_url_ttl_seconds
    )
