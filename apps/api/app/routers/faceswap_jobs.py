import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.auth_dependencies import require_current_user
from app.db import get_session
from app.models.user import AppUser
from app.schemas.faceswap_jobs import (
    FaceSwapJobCreatedResponse,
    FaceSwapJobCreateRequest,
    FaceSwapJobResponse,
)
from app.schemas.jobs import InsufficientCreditsResponse, LimitExceededResponse
from app.schemas.user import ErrorResponse
from app.services import faceswap_job_creation, faceswap_job_views
from app.services.faceswap_job_creation import FaceSwapAssetNotFoundError
from app.services.guardrails import DailyJobLimitError
from app.services.image_job_creation import IdempotencyKeyConflictError
from app.services.job_creation import InsufficientCreditsError
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage

router = APIRouter(prefix="/api/v1", tags=["faceswap-jobs"])


@router.post(
    "/faceswap-jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=FaceSwapJobCreatedResponse,
    responses={
        401: {"model": ErrorResponse},
        402: {"model": InsufficientCreditsResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": LimitExceededResponse},
    },
)
async def create_faceswap_job(
    body: FaceSwapJobCreateRequest,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FaceSwapJobCreatedResponse | JSONResponse:
    try:
        created = await faceswap_job_creation.create_faceswap_job(
            session,
            user.id,
            source_asset_id=body.source_asset_id,
            target_asset_id=body.target_asset_id,
            idempotency_key=body.idempotency_key,
        )
    except FaceSwapAssetNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Face swap asset not found") from error
    except IdempotencyKeyConflictError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Idempotency key already belongs to another job type",
        ) from error
    except DailyJobLimitError as error:
        return _limit_response("Daily generation limit reached. Try again tomorrow.", error)
    except InsufficientCreditsError as error:
        return _insufficient_credits_response(error)
    return FaceSwapJobCreatedResponse(
        id=created.id, status=created.status, credit_cost=created.credit_cost
    )


@router.get(
    "/faceswap-jobs/{job_id}",
    response_model=FaceSwapJobResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def read_faceswap_job(
    job_id: uuid.UUID,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FaceSwapJobResponse:
    found = await faceswap_job_views.read_owned_faceswap_job(
        session, storage, settings, user.id, job_id
    )
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return found


def _insufficient_credits_response(error: InsufficientCreditsError) -> JSONResponse:
    body = InsufficientCreditsResponse(
        detail="Not enough credits", balance=error.balance, required=error.required
    )
    return JSONResponse(status_code=status.HTTP_402_PAYMENT_REQUIRED, content=body.model_dump())


def _limit_response(detail: str, error: DailyJobLimitError) -> JSONResponse:
    body = LimitExceededResponse(detail=detail, limit=error.limit, used=error.used)
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body.model_dump())
