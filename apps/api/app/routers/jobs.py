import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.auth_dependencies import require_current_user
from app.db import get_session
from app.domain.credit_rules import PAID_BACKENDS
from app.job_event_dependencies import get_job_event_broker
from app.models.user import AppUser
from app.repositories.jobs import find_owned_job
from app.schemas.jobs import (
    InsufficientCreditsResponse,
    JobCreatedResponse,
    JobCreateRequest,
    JobResponse,
    JobStatusEvent,
    LibraryListResponse,
    LimitExceededResponse,
    PaidBudgetExceededResponse,
)
from app.schemas.user import ErrorResponse
from app.services import job_creation
from app.services.guardrails import DailyJobLimitError, PaidBudgetExceededError
from app.services.job_creation import (
    InputAssetNotFoundError,
    InputAssetNotReadyError,
    InsufficientCreditsError,
    PresetNotFoundError,
)
from app.services.job_event_stream import stream_job_status_events
from app.services.job_views import (
    JobView,
    list_owned_jobs_view,
    read_owned_job,
    to_library_item_response,
)
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage

router = APIRouter(prefix="/api/v1", tags=["jobs"])


class EventStreamResponse(StreamingResponse):
    media_type = "text/event-stream"


NOT_OWNED_RESPONSE: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse, "description": "Unknown job or not the caller's"},
}
JOB_EVENT_STREAM_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {"model": JobStatusEvent, "description": "SSE status frames of JobStatusEvent, `: ping` every 20s"},
    **NOT_OWNED_RESPONSE,
}


@router.post(
    "/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobCreatedResponse,
    responses={
        401: {"model": ErrorResponse},
        402: {"model": InsufficientCreditsResponse},
        404: {"model": ErrorResponse, "description": "Unknown preset or input asset"},
        409: {"model": ErrorResponse, "description": "Input asset upload not completed"},
    },
)
async def create_job(
    body: JobCreateRequest,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobCreatedResponse | JSONResponse:
    try:
        created = await job_creation.create_job(
            session,
            user.id,
            preset_slug=body.preset_slug,
            input_asset_id=body.input_asset_id,
            prompt=body.prompt,
            idempotency_key=body.idempotency_key,
            is_paid_backend=settings.generation_backend in PAID_BACKENDS,
            paid_budget_cents=settings.paid_budget_cents,
        )
    except PresetNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Preset not found") from error
    except InputAssetNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Input asset not found") from error
    except InputAssetNotReadyError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, "Input asset upload not completed") from error
    except DailyJobLimitError as error:
        return _limit_response("Daily generation limit reached. Try again tomorrow.", error)
    except PaidBudgetExceededError as error:
        return _budget_response(error)
    except InsufficientCreditsError as error:
        return _insufficient_credits_response(error)
    return JobCreatedResponse(id=created.id, status=created.status, credit_cost=created.credit_cost)


@router.get(
    "/jobs",
    response_model=LibraryListResponse,
    responses={401: {"model": ErrorResponse}},
)
async def list_jobs(
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> LibraryListResponse:
    views = await list_owned_jobs_view(session, storage, settings, user.id, limit)
    return LibraryListResponse(
        items=[to_library_item_response(view) for view in views]
    )


@router.get("/jobs/{job_id}", responses=NOT_OWNED_RESPONSE)
async def read_job(
    job_id: uuid.UUID,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobResponse:
    view = await read_owned_job(session, storage, settings, user.id, job_id)
    if view is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return build_job_response(view)


@router.get("/jobs/{job_id}/events", response_class=EventStreamResponse, responses=JOB_EVENT_STREAM_RESPONSE)
async def stream_job_events(
    job_id: uuid.UUID,
    request: Request,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventStreamResponse:
    # Ownership only: an image job has no preset/input for read_owned_job to describe.
    if await find_owned_job(session, user.id, job_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    # resolved after the ownership check so a non-owner always gets plain JSON 404
    broker = await get_job_event_broker(request)
    events = stream_job_status_events(job_id, broker, request.app.state.session_maker)
    return EventStreamResponse(events, headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _insufficient_credits_response(error: InsufficientCreditsError) -> JSONResponse:
    body = InsufficientCreditsResponse(
        detail="Not enough credits", balance=error.balance, required=error.required
    )
    return JSONResponse(status_code=status.HTTP_402_PAYMENT_REQUIRED, content=body.model_dump())


def _limit_response(detail: str, error: DailyJobLimitError) -> JSONResponse:
    body = LimitExceededResponse(detail=detail, limit=error.limit, used=error.used)
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body.model_dump())


def _budget_response(error: PaidBudgetExceededError) -> JSONResponse:
    body = PaidBudgetExceededResponse(
        detail="The AI budget for today is used up; try again later.",
        spent_cents=error.spent_cents,
        budget_cents=error.budget_cents,
    )
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body.model_dump())


def build_job_response(view: JobView) -> JobResponse:
    job = view.job
    return JobResponse(
        id=job.id,
        status=job.status,
        preset_slug=job.preset_slug,
        preset_name=view.preset_name,
        prompt=job.prompt,
        credit_cost=job.credit_cost,
        input_asset_id=job.input_asset_id,
        input_image_url=view.input_image_url,
        video_url=view.video_url,
        poster_url=view.poster_url,
        generated_by=job.generated_by,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
