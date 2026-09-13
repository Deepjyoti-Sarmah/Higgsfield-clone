from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.db import get_session
from app.schemas.presets import PresetListResponse, PresetResponse
from app.services.presets import preview_url_for, read_presets
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage

router = APIRouter(prefix="/api/v1", tags=["presets"])


@router.get("/presets")
async def list_presets(
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PresetListResponse:
    presets = await read_presets(session, storage, settings)
    return PresetListResponse(
        presets=[
            PresetResponse(
                slug=preset.slug,
                name=preset.name,
                description=preset.description,
                category=preset.category,
                credit_cost=preset.credit_cost,
                preview_url=preview_url_for(preset, storage, settings),
            )
            for preset in presets
        ]
    )
