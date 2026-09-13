import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.auth_dependencies import require_current_user
from app.db import get_session
from app.models.user import AppUser
from app.schemas.uploads import AssetResponse, UploadCreateRequest, UploadCreateResponse
from app.schemas.user import ErrorResponse
from app.services.uploads import (
    UploadNotFoundError,
    UploadObjectMissingError,
    UploadSizeMismatchError,
    create_pending_upload,
    mark_upload_complete,
)
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage

router = APIRouter(prefix="/api/v1", tags=["uploads"])


@router.post("/uploads", status_code=status.HTTP_201_CREATED, responses={401: {"model": ErrorResponse}})
async def create_upload(
    body: UploadCreateRequest,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadCreateResponse:
    pending = await create_pending_upload(
        session,
        storage,
        settings,
        user_id=user.id,
        content_type=body.content_type,
        byte_size=body.byte_size,
    )
    return UploadCreateResponse(
        asset_id=pending.asset.id,
        upload_url=pending.upload_url,
        upload_headers={"Content-Type": pending.asset.content_type},
        expires_at=pending.expires_at,
    )


@router.post(
    "/uploads/{asset_id}/complete",
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Unknown asset or not the caller's"},
        409: {"model": ErrorResponse, "description": "Object not found in storage yet"},
    },
)
async def complete_upload(
    asset_id: uuid.UUID,
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AssetResponse:
    try:
        completed = await mark_upload_complete(
            session, storage, settings, user_id=user.id, asset_id=asset_id
        )
    except UploadNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found") from error
    except UploadObjectMissingError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, "Upload not found in storage") from error
    except UploadSizeMismatchError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Uploaded file does not match the declared size",
        ) from error
    asset = completed.asset
    return AssetResponse(
        id=asset.id,
        kind=asset.kind,
        status=asset.status,
        content_type=asset.content_type,
        byte_size=asset.byte_size,
        url=completed.url,
    )
