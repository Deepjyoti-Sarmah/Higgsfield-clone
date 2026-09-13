from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_dependencies import require_current_user
from app.models.user import AppUser
from app.schemas.credits import CreditsResponse
from app.schemas.user import ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["credits"])


@router.get("/credits", responses={401: {"model": ErrorResponse}})
async def read_credits(user: Annotated[AppUser, Depends(require_current_user)]) -> CreditsResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented")
