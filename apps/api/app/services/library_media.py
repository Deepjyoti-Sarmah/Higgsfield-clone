import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage, build_asset_url
from app.models.asset import Asset
from app.models.job import Job
from app.models.job_image import JobImage
from app.repositories.assets import find_assets_by_ids
from app.settings import Settings


async def find_images_by_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    jobs: list[Job],
) -> dict[uuid.UUID, list[tuple[uuid.UUID, str]]]:
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
    images_by_job: dict[uuid.UUID, list[tuple[uuid.UUID, str]]] = {job_id: [] for job_id in image_job_ids}
    for image in job_images:
        url = asset_url(storage, settings, assets, image.asset_id)
        if url is not None:
            images_by_job[image.job_id].append((image.asset_id, url))
    return images_by_job


async def find_image_urls_by_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    jobs: list[Job],
) -> dict[uuid.UUID, list[str]]:
    images_by_job = await find_images_by_job(session, storage, settings, jobs)
    return {job_id: [url for _, url in images] for job_id, images in images_by_job.items()}


def asset_url(
    storage: ObjectStorage,
    settings: Settings,
    assets: dict[uuid.UUID, Asset],
    asset_id: uuid.UUID | None,
) -> str | None:
    return None if asset_id is None else ready_url(storage, settings, assets.get(asset_id))


def ready_url(storage: ObjectStorage, settings: Settings, asset: Asset | None) -> str | None:
    if asset is None or asset.status != "ready":
        return None
    return build_asset_url(
        storage, asset.storage_key, settings.s3_public_base_url, settings.download_url_ttl_seconds
    )
