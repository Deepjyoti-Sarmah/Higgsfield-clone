import uuid
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.repositories.assets import find_assets_by_ids
from app.repositories.video_faceswap_jobs import find_owned_video_faceswap_job
from app.schemas.jobs import JobStatus
from app.schemas.video_faceswap_jobs import VideoFaceSwapJobResponse
from app.services.library_media import asset_url, ready_url
from app.settings import Settings


async def read_owned_video_faceswap_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> VideoFaceSwapJobResponse | None:
    job = await find_owned_video_faceswap_job(session, user_id, job_id)
    if job is None or job.face_source_asset_id is None or job.face_target_asset_id is None:
        return None
    wanted = [job.face_source_asset_id, job.face_target_asset_id]
    if job.output_video_asset_id is not None:
        wanted.append(job.output_video_asset_id)
    if job.output_poster_asset_id is not None:
        wanted.append(job.output_poster_asset_id)
    assets = await find_assets_by_ids(session, wanted)
    video_url = None
    poster_url = None
    if job.status == "succeeded":
        video_url = asset_url(storage, settings, assets, job.output_video_asset_id)
        poster_url = asset_url(storage, settings, assets, job.output_poster_asset_id)
    return VideoFaceSwapJobResponse(
        id=job.id,
        status=cast("JobStatus", job.status),
        credit_cost=job.credit_cost,
        source_url=ready_url(storage, settings, assets.get(job.face_source_asset_id)),
        target_url=ready_url(storage, settings, assets.get(job.face_target_asset_id)),
        video_url=video_url,
        poster_url=poster_url,
        duration_ms=job.duration_ms,
        generated_by=job.generated_by,
        error_message=job.error_message,
        created_at=job.created_at,
    )
