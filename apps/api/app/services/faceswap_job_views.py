import uuid
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.repositories.assets import find_assets_by_ids
from app.repositories.faceswap_jobs import find_owned_faceswap_job
from app.repositories.image_jobs import list_job_images
from app.schemas.faceswap_jobs import FaceSwapJobResponse
from app.schemas.jobs import JobStatus
from app.services.library_media import ready_url
from app.settings import Settings


async def read_owned_faceswap_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> FaceSwapJobResponse | None:
    job = await find_owned_faceswap_job(session, user_id, job_id)
    if job is None or job.face_source_asset_id is None or job.face_target_asset_id is None:
        return None
    images = await list_job_images(session, job_id)
    image_asset_id = next((image.asset_id for image in images if image.position == 0), None)
    wanted = [job.face_source_asset_id, job.face_target_asset_id]
    if image_asset_id is not None:
        wanted.append(image_asset_id)
    assets = await find_assets_by_ids(session, wanted)
    image_url = None
    if job.status == "succeeded" and image_asset_id is not None:
        image_url = ready_url(storage, settings, assets.get(image_asset_id))
    return FaceSwapJobResponse(
        id=job.id,
        status=cast("JobStatus", job.status),
        credit_cost=job.credit_cost,
        source_url=ready_url(storage, settings, assets.get(job.face_source_asset_id)),
        target_url=ready_url(storage, settings, assets.get(job.face_target_asset_id)),
        image_url=image_url,
        generated_by=job.generated_by,
        error_message=job.error_message,
        created_at=job.created_at,
    )
