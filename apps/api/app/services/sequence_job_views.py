import uuid
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage, build_asset_url
from app.models.asset import Asset
from app.repositories.assets import find_assets_by_ids
from app.repositories.sequence_jobs import find_owned_sequence_job, list_sequence_clips
from app.schemas.jobs import JobStatus
from app.schemas.sequence_jobs import (
    SequenceClipResponse,
    SequenceJobResponse,
    SequenceTransition,
)
from app.settings import Settings


def _ready_url(storage: ObjectStorage, settings: Settings, asset: Asset | None) -> str | None:
    if asset is None or asset.status != "ready":
        return None
    return build_asset_url(
        storage, asset.storage_key, settings.s3_public_base_url, settings.download_url_ttl_seconds
    )


async def read_owned_sequence_job(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> SequenceJobResponse | None:
    job = await find_owned_sequence_job(session, user_id, job_id)
    if job is None:
        return None
    clips = await list_sequence_clips(session, job_id)
    wanted = [poster_id for _, poster_id in clips if poster_id is not None]
    wanted += [asset_id for asset_id in (job.output_video_asset_id, job.output_poster_asset_id)
               if asset_id is not None]
    assets = await find_assets_by_ids(session, wanted)
    clip_rows = [
        SequenceClipResponse(
            position=clip.position,
            job_id=clip.source_job_id,
            transition_in=cast("SequenceTransition", clip.transition_in),
            trim_start_ms=clip.trim_start_ms,
            trim_end_ms=clip.trim_end_ms,
            thumbnail_url=_ready_url(storage, settings, assets.get(poster_id))
            if poster_id is not None
            else None,
        )
        for clip, poster_id in clips
    ]
    video_url = None
    poster_url = None
    if job.status == "succeeded":
        if job.output_video_asset_id is not None:
            video_url = _ready_url(
                storage, settings, assets.get(job.output_video_asset_id)
            )
        if job.output_poster_asset_id is not None:
            poster_url = _ready_url(
                storage, settings, assets.get(job.output_poster_asset_id)
            )
    return SequenceJobResponse(
        id=job.id,
        status=cast("JobStatus", job.status),
        credit_cost=job.credit_cost,
        clips=clip_rows,
        has_audio=job.audio_asset_id is not None,
        video_url=video_url,
        poster_url=poster_url,
        duration_ms=job.duration_ms,
        generated_by=job.generated_by,
        error_message=job.error_message,
        created_at=job.created_at,
    )
