import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.share import PublicJobResponse
from app.schemas.user import ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["share"])


# T-007-0 stub for the public share contract. T-007-1 replaces the body: keep this
# handler name, signature and responses map so openapi.json stays byte-identical.
@router.get(
    "/public/jobs/{job_id}",
    response_model=PublicJobResponse,
    responses={404: {"model": ErrorResponse}},
)
async def read_public_job(
    job_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PublicJobResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")
