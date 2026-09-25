import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.models.job import Job
from app.repositories.assets import find_assets_by_ids
from app.repositories.jobs import find_job
from app.repositories.presets import find_active_preset
from app.repositories.sequence_jobs import count_clips_by_job
from app.services import library_media
from app.settings import Settings


@dataclass(frozen=True)
class PublicJobView:
    job: Job
    preset_name: str | None
    poster_url: str | None
    video_url: str | None
    image_urls: list[str] = field(default_factory=list)
    clip_count: int | None = None
    duration_ms: int | None = None


async def read_public_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    job_id: uuid.UUID,
) -> PublicJobView | None:
    job = await find_job(session, job_id)
    if job is None:
        return None
    preset = await find_active_preset(session, job.preset_slug) if job.preset_slug else None
    asset_ids = [
        asset_id
        for asset_id in (job.output_video_asset_id, job.output_poster_asset_id)
        if asset_id is not None
    ]
    assets = await find_assets_by_ids(session, asset_ids)
    extras = await _kind_extras(session, storage, settings, job)
    preset_name = job.preset_slug if preset is None else preset.name
    return PublicJobView(
        job=job,
        preset_name=preset_name,
        poster_url=library_media.asset_url(storage, settings, assets, job.output_poster_asset_id),
        video_url=library_media.asset_url(storage, settings, assets, job.output_video_asset_id),
        image_urls=extras.image_urls,
        clip_count=extras.clip_count,
        duration_ms=extras.duration_ms,
    )


async def _kind_extras(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    job: Job,
) -> PublicJobView:
    image_urls = await _image_urls(session, storage, settings, job) if job.kind == "image" else []
    counts = await count_clips_by_job(session, [job.id]) if job.kind == "sequence" else {}
    return PublicJobView(
        job=job,
        preset_name=None,
        poster_url=None,
        video_url=None,
        image_urls=image_urls,
        clip_count=counts.get(job.id),
        duration_ms=job.duration_ms if job.kind == "sequence" else None,
    )


async def _image_urls(
    session: AsyncSession, storage: ObjectStorage, settings: Settings, job: Job
) -> list[str]:
    urls_by_job = await library_media.find_image_urls_by_job(session, storage, settings, [job])
    return urls_by_job.get(job.id, [])

