from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.db import get_session
from app.schemas.health import DeepHealthResponse, HealthCheckResponse
from app.schemas.user import HealthResponse
from app.services.system_health import collect_deep_health, is_database_reachable
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", responses={503: {"model": HealthResponse}})
async def read_health(
    response: Response, session: Annotated[AsyncSession, Depends(get_session)]
) -> HealthResponse:
    if await is_database_reachable(session):
        return HealthResponse(status="ok", database="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="degraded", database="down")


@router.get("/health/deep", responses={503: {"model": DeepHealthResponse}})
async def read_deep_health(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DeepHealthResponse:
    health = await collect_deep_health(session, storage, settings)
    if health.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return DeepHealthResponse(
        status=health.status,
        duration_ms=health.duration_ms,
        checks={
            name: HealthCheckResponse(
                status=check.status, duration_ms=check.duration_ms, detail=check.detail
            )
            for name, check in health.checks.items()
        },
    )
