from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.user import HealthResponse
from app.services.system_health import is_database_reachable

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", responses={503: {"model": HealthResponse}})
async def read_health(
    response: Response, session: Annotated[AsyncSession, Depends(get_session)]
) -> HealthResponse:
    if await is_database_reachable(session):
        return HealthResponse(status="ok", database="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="degraded", database="down")
