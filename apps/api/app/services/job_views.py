import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage, build_asset_url
from app.models.asset import Asset
from app.models.job import Job
from app.models.job_image import JobImage
from app.repositories.assets import find_assets_by_ids
from app.repositories.jobs import find_user_job, list_owned_jobs
from app.repositories.presets import find_active_preset, list_active_presets
from app.schemas.jobs import LibraryItemResponse
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
    """Kind-agnostic: builds one Library row per job, video or image."""
    jobs = await list_owned_jobs(session, user_id, limit)
    if not jobs:
        return []
    preset_names = {preset.slug: preset.name for preset in await list_active_presets(session)}
    assets = await find_assets_by_ids(session, _referenced_asset_ids(jobs))
    image_urls_by_job = await _find_image_urls_by_job(session, storage, settings, jobs)
    return [
        _library_item_view(storage, settings, job, preset_names, assets, image_urls_by_job)
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


async def _find_image_urls_by_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    jobs: list[Job],
) -> dict[uuid.UUID, list[str]]:
    image_job_ids = [job.id for job in jobs if job.kind == "image"]
    if not image_job_ids:
        return {}
    result = await session.execute(
        select(JobImage)
        .where(JobImage.job_id.in_(image_job_ids))
        .order_by(JobImage.job_id, JobImage.position)
    )
    job_images = list(result.scalars())
    assets = await find_assets_by_ids(session, [image.asset_id for image in job_images])
    urls_by_job: dict[uuid.UUID, list[str]] = {job_id: [] for job_id in image_job_ids}
    for image in job_images:
        url = _asset_url(storage, settings, assets, image.asset_id)
        if url is not None:
            urls_by_job[image.job_id].append(url)
    return urls_by_job


def _library_item_view(
    storage: ObjectStorage,
    settings: Settings,
    job: Job,
    preset_names: dict[str, str],
    assets: dict[uuid.UUID, Asset],
    image_urls_by_job: dict[uuid.UUID, list[str]],
) -> LibraryItemView:
    if job.kind == "image":
        image_urls = image_urls_by_job.get(job.id, [])
        return LibraryItemView(
            job=job,
            preset_name=None,
            generated_by=job.generated_by,
            thumbnail_url=image_urls[0] if image_urls else None,
            video_url=None,
            image_urls=image_urls,
        )
    poster_url = _asset_url(storage, settings, assets, job.output_poster_asset_id)
    input_url = _asset_url(storage, settings, assets, job.input_asset_id)
    preset_slug = job.preset_slug
    return LibraryItemView(
        job=job,
        preset_name=None if preset_slug is None else preset_names.get(preset_slug, preset_slug),
        generated_by=job.generated_by,
        thumbnail_url=poster_url or input_url,
        video_url=_asset_url(storage, settings, assets, job.output_video_asset_id),
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
        generated_by=view.generated_by,
        created_at=view.job.created_at,
        error_message=view.job.error_message,
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
