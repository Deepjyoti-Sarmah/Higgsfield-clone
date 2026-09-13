import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_dependencies import require_current_user
from app.models.user import AppUser
from app.schemas.uploads import AssetResponse, UploadCreateRequest, UploadCreateResponse
from app.schemas.user import ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["uploads"])


@router.post("/uploads", status_code=status.HTTP_201_CREATED, responses={401: {"model": ErrorResponse}})
async def create_upload(
    body: UploadCreateRequest, user: Annotated[AppUser, Depends(require_current_user)]
) -> UploadCreateResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")


@router.post(
    "/uploads/{asset_id}/complete",
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Unknown asset or not the caller's"},
        409: {"model": ErrorResponse, "description": "Object not found in storage yet"},
    },
)
async def complete_upload(
    asset_id: uuid.UUID, user: Annotated[AppUser, Depends(require_current_user)]
) -> AssetResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")
