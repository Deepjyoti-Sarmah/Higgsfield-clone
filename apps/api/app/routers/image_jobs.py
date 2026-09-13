import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_dependencies import require_current_user
from app.db import get_session
from app.models.user import AppUser
from app.schemas.image_jobs import (
    ImageJobCreatedResponse,
    ImageJobCreateRequest,
    ImageJobResponse,
    ImageOptionsResponse,
)
from app.schemas.jobs import InsufficientCreditsResponse
from app.schemas.user import ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["image-jobs"])


# T-009-0 stubs for the image contract. T-009-4 replaces the bodies: keep these handler
# names, signatures, status codes and responses maps so openapi.json stays byte-identical.
@router.get("/image-options", response_model=ImageOptionsResponse)
async def read_image_options() -> ImageOptionsResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")


@router.post(
    "/image-jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ImageJobCreatedResponse,
    responses={
        401: {"model": ErrorResponse},
        402: {"model": InsufficientCreditsResponse},
    },
)
async def create_image_job(
    body: ImageJobCreateRequest,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ImageJobCreatedResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")


@router.get(
    "/image-jobs/{job_id}",
    response_model=ImageJobResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Unknown job or not the caller's"},
    },
)
async def read_image_job(
    job_id: uuid.UUID,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ImageJobResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")
