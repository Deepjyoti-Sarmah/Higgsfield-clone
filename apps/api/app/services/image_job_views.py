import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage, build_asset_url
from app.models.asset import Asset
from app.models.job import Job
from app.repositories.assets import find_assets_by_ids
from app.repositories.image_jobs import find_job_backend, find_owned_image_job, list_job_images
from app.settings import Settings


@dataclass(frozen=True)
class ImageJobView:
    job: Job
    backend: str | None
    image_urls: list[str]


async def read_owned_image_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> ImageJobView | None:
    job = await find_owned_image_job(session, user_id, job_id)
    if job is None:
        return None
    images = await list_job_images(session, job_id)
    assets = await find_assets_by_ids(session, [image.asset_id for image in images])
    urls: list[str] = []
    for image in images:
        url = _ready_url(storage, settings, assets.get(image.asset_id))
        if url is not None:
            urls.append(url)
    return ImageJobView(job=job, backend=await find_job_backend(session, job_id), image_urls=urls)


def _ready_url(storage: ObjectStorage, settings: Settings, asset: Asset | None) -> str | None:
    if asset is None or asset.status != "ready":
        return None
    return build_asset_url(
        storage, asset.storage_key, settings.s3_public_base_url, settings.download_url_ttl_seconds
    )
