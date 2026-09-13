import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage, build_asset_url
from app.models.asset import Asset
from app.models.job import Job
from app.repositories.assets import find_assets_by_ids
from app.repositories.jobs import find_user_job, list_owned_jobs
from app.repositories.presets import find_active_preset, list_active_presets
from app.settings import Settings


@dataclass(frozen=True)
class JobView:
    job: Job
    preset_name: str
    input_image_url: str | None
    video_url: str | None
    poster_url: str | None


@dataclass(frozen=True)
class LibraryItemView:
    job: Job
    preset_name: str
    thumbnail_url: str | None
    video_url: str | None


async def read_owned_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> JobView | None:
    job = await find_user_job(session, user_id, job_id)
    if job is None or job.preset_slug is None or job.input_asset_id is None:
        return None
    preset = await find_active_preset(session, job.preset_slug)
    output_ids = [job.output_video_asset_id, job.output_poster_asset_id]
    assets = await find_assets_by_ids(
        session, [job.input_asset_id, *(asset_id for asset_id in output_ids if asset_id)]
    )
    return JobView(
        job=job,
        preset_name=job.preset_slug if preset is None else preset.name,
        input_image_url=_ready_url(storage, settings, assets.get(job.input_asset_id)),
        video_url=_asset_url(storage, settings, assets, job.output_video_asset_id),
        poster_url=_asset_url(storage, settings, assets, job.output_poster_asset_id),
    )


async def list_owned_jobs_view(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    user_id: uuid.UUID,
    limit: int,
) -> list[LibraryItemView]:
    jobs = await list_owned_jobs(session, user_id, limit)
    if not jobs:
        return []
    preset_names = {preset.slug: preset.name for preset in await list_active_presets(session)}
    assets = await find_assets_by_ids(session, _referenced_asset_ids(jobs))
    items: list[LibraryItemView] = []
    for job in jobs:
        if job.preset_slug is None:
            continue
        items.append(
            _library_item_view(storage, settings, job, job.preset_slug, preset_names, assets)
        )
    return items


def _referenced_asset_ids(jobs: list[Job]) -> list[uuid.UUID]:
    ids = [job.input_asset_id for job in jobs if job.input_asset_id is not None]
    ids.extend(
        asset_id
        for job in jobs
        for asset_id in (job.output_video_asset_id, job.output_poster_asset_id)
        if asset_id is not None
    )
    return ids


def _library_item_view(
    storage: ObjectStorage,
    settings: Settings,
    job: Job,
    preset_slug: str,
    preset_names: dict[str, str],
    assets: dict[uuid.UUID, Asset],
) -> LibraryItemView:
    poster_url = _asset_url(storage, settings, assets, job.output_poster_asset_id)
    input_url = _asset_url(storage, settings, assets, job.input_asset_id)
    return LibraryItemView(
        job=job,
        preset_name=preset_names.get(preset_slug, preset_slug),
        thumbnail_url=poster_url or input_url,
        video_url=_asset_url(storage, settings, assets, job.output_video_asset_id),
    )


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
