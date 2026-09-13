import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.assets import find_user_asset
from app.repositories.job_steps import ClaimedStep
from app.repositories.jobs import find_job


@dataclass(frozen=True)
class StepInputs:
    user_id: uuid.UUID
    preset_slug: str
    prompt: str | None
    input_key: str


async def load_step_inputs(
    session_maker: async_sessionmaker[AsyncSession], claimed: ClaimedStep
) -> StepInputs | None:
    async with session_maker() as session:
        job = await find_job(session, claimed.job_id)
        # The video run needs both video-only columns; an image step never reaches here.
        if job is None or job.input_asset_id is None or job.preset_slug is None:
            return None
        asset = await find_user_asset(session, job.user_id, job.input_asset_id)
        if asset is None:
            return None
        return StepInputs(
            user_id=job.user_id,
            preset_slug=job.preset_slug,
            prompt=job.prompt,
            input_key=asset.storage_key,
        )
