import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.repositories.assets import find_assets_by_ids, find_user_asset
from app.repositories.jobs import find_job
from app.repositories.sequence_jobs import find_clip_source_jobs, list_sequence_clips


@dataclass(frozen=True)
class StitchClipInput:
    storage_key: str
    transition_in: str


@dataclass(frozen=True)
class StitchInputs:
    user_id: uuid.UUID
    job_id: uuid.UUID
    clips: list[StitchClipInput]
    audio_storage_key: str | None


async def load_stitch_inputs(session: AsyncSession, job_id: uuid.UUID) -> StitchInputs | None:
    job = await find_job(session, job_id)
    if job is None or job.kind != "sequence":
        return None
    clips = await list_sequence_clips(session, job_id)
    if not clips:
        return None
    sources = await find_clip_source_jobs(
        session, job.user_id, [clip.source_job_id for clip, _ in clips]
    )
    wanted = [video_id for clip, _ in clips
              if (video_id := _source_video_id(sources, clip.source_job_id)) is not None]
    if len(wanted) != len(clips):
        return None
    assets = await find_assets_by_ids(session, wanted)
    stitched: list[StitchClipInput] = []
    for (clip, _), video_id in zip(clips, wanted, strict=True):
        asset = assets.get(video_id)
        if asset is None:
            return None
        stitched.append(StitchClipInput(storage_key=asset.storage_key,
                                        transition_in=clip.transition_in))
    return StitchInputs(user_id=job.user_id, job_id=job.id, clips=stitched,
                        audio_storage_key=await _audio_key(session, job))


def _source_video_id(sources: dict[uuid.UUID, Job], source_id: uuid.UUID) -> uuid.UUID | None:
    source = sources.get(source_id)
    if source is None:
        return None
    return source.output_video_asset_id


async def _audio_key(session: AsyncSession, job: Job) -> str | None:
    if job.audio_asset_id is None:
        return None
    asset = await find_user_asset(session, job.user_id, job.audio_asset_id)
    if asset is None:
        return None
    return asset.storage_key
