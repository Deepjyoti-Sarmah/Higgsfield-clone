import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.models.asset import Asset
from app.models.job import Job
from app.repositories.assets import find_assets_by_ids
from app.repositories.jobs import find_user_job, list_owned_jobs
from app.repositories.presets import find_active_preset, list_active_presets
from app.repositories.sequence_jobs import count_clips_by_job
from app.schemas.jobs import LibraryImageResponse, LibraryItemResponse
from app.services import library_media
from app.services.library_media import STILL_LIKE_KINDS
from app.settings import Settings


@dataclass(frozen=True)
class JobView:
    job: Job
    preset_name: str
    generated_by: str | None
    input_image_url: str | None
    video_url: str | None
    poster_url: str | None


@dataclass(frozen=True)
class LibraryItemView:
    job: Job
    preset_name: str | None
    generated_by: str | None
    thumbnail_url: str | None
    video_url: str | None
    image_urls: list[str] = field(default_factory=list)
    images: list[tuple[uuid.UUID, str]] = field(default_factory=list)
    clip_count: int | None = None
    duration_ms: int | None = None


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
        generated_by=job.generated_by,
        input_image_url=library_media.ready_url(storage, settings, assets.get(job.input_asset_id)),
        video_url=library_media.asset_url(storage, settings, assets, job.output_video_asset_id),
        poster_url=library_media.asset_url(storage, settings, assets, job.output_poster_asset_id),
    )


async def list_owned_jobs_view(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    user_id: uuid.UUID,
    limit: int,
) -> list[LibraryItemView]:
    """Kind-agnostic: builds one Library row per job, video, image or sequence."""
    jobs = await list_owned_jobs(session, user_id, limit)
    if not jobs:
        return []
    preset_names = {preset.slug: preset.name for preset in await list_active_presets(session)}
    assets = await find_assets_by_ids(session, _referenced_asset_ids(jobs))
    images_by_job = await library_media.find_images_by_job(session, storage, settings, jobs)
    clip_counts = await count_clips_by_job(session, [job.id for job in jobs])
    return [
        _library_item_view(
            storage, settings, job, preset_names, assets, images_by_job, clip_counts,
        )
        for job in jobs
    ]


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
    preset_names: dict[str, str],
    assets: dict[uuid.UUID, Asset],
    images_by_job: dict[uuid.UUID, list[tuple[uuid.UUID, str]]],
    clip_counts: dict[uuid.UUID, int],
) -> LibraryItemView:
    if job.kind in STILL_LIKE_KINDS:
        images = images_by_job.get(job.id, [])
        image_urls = [url for _, url in images]
        return LibraryItemView(
            job=job,
            preset_name=None,
            generated_by=job.generated_by,
            thumbnail_url=image_urls[0] if image_urls else None,
            video_url=None,
            image_urls=image_urls,
            images=images,
        )
    poster_url = library_media.asset_url(storage, settings, assets, job.output_poster_asset_id)
    input_url = library_media.asset_url(storage, settings, assets, job.input_asset_id)
    preset_slug = job.preset_slug
    return LibraryItemView(
        job=job,
        preset_name=None if preset_slug is None else preset_names.get(preset_slug, preset_slug),
        generated_by=job.generated_by,
        thumbnail_url=poster_url or input_url,
        video_url=library_media.asset_url(storage, settings, assets, job.output_video_asset_id),
        clip_count=clip_counts.get(job.id),
        duration_ms=job.duration_ms,
    )


def to_library_item_response(view: LibraryItemView) -> LibraryItemResponse:
    return LibraryItemResponse(
        id=view.job.id,
        kind=view.job.kind,  # type: ignore[arg-type]
        status=view.job.status,  # type: ignore[arg-type]
        preset_slug=view.job.preset_slug,
        preset_name=view.preset_name,
        prompt=view.job.prompt,
        thumbnail_url=view.thumbnail_url,
        video_url=view.video_url,
        image_urls=view.image_urls,
        images=[LibraryImageResponse(asset_id=asset_id, url=url) for asset_id, url in view.images],
        clip_count=view.clip_count,
        duration_ms=view.duration_ms,
        generated_by=view.generated_by,
        created_at=view.job.created_at,
        error_message=view.job.error_message,
    )
