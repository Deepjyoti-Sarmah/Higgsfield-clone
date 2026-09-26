import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.asset import Asset
from app.models.job import Job
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import create_queued_job, current_user_id

SessionMaker = async_sessionmaker[AsyncSession]


def build_sequence_body(clip_ids: list[str], key: str, audio_id: str | None = None) -> dict:
    body: dict[str, object] = {
        "clips": [{"job_id": clip_id, "transition_in": "crossfade"} for clip_id in clip_ids],
        "idempotency_key": key,
    }
    if audio_id is not None:
        body["audio_asset_id"] = audio_id
    return body


async def create_succeeded_clip(
    guest_client: AsyncClient, storage: InMemoryObjectStorage, session_maker: SessionMaker, key: str,
) -> str:
    job_id = await create_queued_job(guest_client, storage, key)
    user_id = await current_user_id(guest_client)
    video_id, poster_id = uuid.uuid4(), uuid.uuid4()
    async with session_maker() as session:
        for asset_id, asset_kind, name in (
            (video_id, "output_video", "video.mp4"),
            (poster_id, "output_poster", "poster.jpg"),
        ):
            session.add(Asset(id=asset_id, user_id=uuid.UUID(user_id), kind=asset_kind,
                              status="ready", byte_size=100,
                              storage_key=f"users/{user_id}/jobs/{job_id}/{name}",
                              content_type="video/mp4"))
        job = await session.get(Job, uuid.UUID(job_id))
        assert job is not None
        job.status = "succeeded"
        job.output_video_asset_id = video_id
        job.output_poster_asset_id = poster_id
        await session.commit()
    return job_id


async def create_succeeded_video_faceswap(
    guest_client: AsyncClient, session_maker: SessionMaker, key: str,
) -> str:
    user_id = uuid.UUID(await current_user_id(guest_client))
    face_id, target_id, video_id, poster_id = (uuid.uuid4() for _ in range(4))
    async with session_maker() as session:
        for asset_id, kind, name, content_type in (
            (face_id, "input_image", "face.jpg", "image/jpeg"),
            (target_id, "input_image", "target.jpg", "image/jpeg"),
            (video_id, "output_video", "video.mp4", "video/mp4"),
            (poster_id, "output_poster", "poster.jpg", "image/jpeg"),
        ):
            session.add(Asset(id=asset_id, user_id=user_id, kind=kind, status="ready",
                              byte_size=100,
                              storage_key=f"users/{user_id}/jobs/{asset_id}/{name}",
                              content_type=content_type))
        job = Job(user_id=user_id, kind="video_faceswap", status="succeeded",
                  idempotency_key=key, credit_cost=10, face_source_asset_id=face_id,
                  face_target_asset_id=target_id, output_video_asset_id=video_id,
                  output_poster_asset_id=poster_id)
        session.add(job)
        await session.commit()
        return str(job.id)


async def count_where(session_maker: SessionMaker, table: str, clause: str, job: uuid.UUID) -> int:
    async with session_maker() as session:
        return int(await session.scalar(
            text(f"SELECT count(*) FROM {table} WHERE {clause}"), {"job_id": job}) or 0)


async def clip_rows(session_maker: SessionMaker, job: uuid.UUID) -> list[tuple[int, str]]:
    async with session_maker() as session:
        found = await session.execute(
            text("SELECT position, transition_in FROM job_sequence_clip "
                 "WHERE job_id = :job_id ORDER BY position"), {"job_id": job})
        return [(row[0], row[1]) for row in found]
