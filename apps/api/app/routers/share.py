import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.db import get_session
from app.schemas.share import PublicJobResponse
from app.schemas.user import ErrorResponse
from app.services import share_views
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage

router = APIRouter(prefix="/api/v1", tags=["share"])


@router.get(
    "/public/jobs/{job_id}",
    response_model=PublicJobResponse,
    responses={404: {"model": ErrorResponse}},
)
async def read_public_job(
    job_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PublicJobResponse:
    view = await share_views.read_public_job(session, storage, settings, job_id)
    if view is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return PublicJobResponse(
        id=view.job.id,
        status=view.job.status,
        preset_slug=view.job.preset_slug,
        preset_name=view.preset_name,
        poster_url=view.poster_url,
        video_url=view.video_url,
        created_at=view.job.created_at,
    )
