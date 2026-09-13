from fastapi import APIRouter, HTTPException, status

from app.schemas.presets import PresetListResponse

router = APIRouter(prefix="/api/v1", tags=["presets"])


@router.get("/presets")
async def list_presets() -> PresetListResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")
