import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
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
from app.services import image_job_creation, image_job_views, image_options
from app.services.image_job_creation import IdempotencyKeyConflictError
from app.services.job_creation import InsufficientCreditsError
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage

router = APIRouter(prefix="/api/v1", tags=["image-jobs"])


@router.get("/image-options", response_model=ImageOptionsResponse)
async def read_image_options() -> ImageOptionsResponse:
    return image_options.read_image_options()


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
) -> ImageJobCreatedResponse | JSONResponse:
    try:
        created = await image_job_creation.create_image_job(
            session,
            user.id,
            prompt=body.prompt,
            aspect_ratio=body.aspect_ratio,
            quality=body.quality,
            count=body.count,
            idempotency_key=body.idempotency_key,
        )
    except IdempotencyKeyConflictError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Idempotency key already belongs to another job type",
        ) from error
    except InsufficientCreditsError as error:
        return _insufficient_credits_response(error)
    return ImageJobCreatedResponse(
        id=created.id,
        status=created.status,
        credit_cost=created.credit_cost,
        image_count=created.image_count,
    )


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
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ImageJobResponse:
    view = await image_job_views.read_owned_image_job(session, storage, settings, user.id, job_id)
    if view is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    job = view.job
    return ImageJobResponse(
        id=job.id,
        status=job.status,
        prompt=job.prompt or "",
        aspect_ratio=job.aspect_ratio,
        quality=job.quality,
        count=job.image_count or 0,
        credit_cost=job.credit_cost,
        backend=view.backend,
        image_urls=view.image_urls,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _insufficient_credits_response(error: InsufficientCreditsError) -> JSONResponse:
    body = InsufficientCreditsResponse(
        detail="Not enough credits", balance=error.balance, required=error.required
    )
    return JSONResponse(status_code=status.HTTP_402_PAYMENT_REQUIRED, content=body.model_dump())
