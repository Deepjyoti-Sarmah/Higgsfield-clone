import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.auth_dependencies import require_current_user
from app.models.user import AppUser
from app.schemas.jobs import (
    InsufficientCreditsResponse,
    JobCreatedResponse,
    JobCreateRequest,
    JobResponse,
    JobStatusEvent,
)
from app.schemas.user import ErrorResponse

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
    responses={
        401: {"model": ErrorResponse},
        402: {"model": InsufficientCreditsResponse},
        404: {"model": ErrorResponse, "description": "Unknown preset or input asset"},
        409: {"model": ErrorResponse, "description": "Input asset upload not completed"},
    },
)
async def create_job(
    body: JobCreateRequest, user: Annotated[AppUser, Depends(require_current_user)]
) -> JobCreatedResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")


@router.get("/jobs/{job_id}", responses=NOT_OWNED_RESPONSE)
async def read_job(job_id: uuid.UUID, user: Annotated[AppUser, Depends(require_current_user)]) -> JobResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")


@router.get("/jobs/{job_id}/events", response_class=EventStreamResponse, responses=JOB_EVENT_STREAM_RESPONSE)
async def stream_job_events(
    job_id: uuid.UUID, user: Annotated[AppUser, Depends(require_current_user)]
) -> EventStreamResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")

