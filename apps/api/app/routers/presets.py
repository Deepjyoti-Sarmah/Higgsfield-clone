from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.presets import PresetListResponse, PresetResponse
from app.services.presets import read_presets

router = APIRouter(prefix="/api/v1", tags=["presets"])


@router.get("/presets")
async def list_presets(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PresetListResponse:
    presets = await read_presets(session)
    return PresetListResponse(presets=[PresetResponse.model_validate(preset) for preset in presets])
