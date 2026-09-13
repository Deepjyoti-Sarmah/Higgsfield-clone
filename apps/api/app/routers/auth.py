from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_dependencies import SESSION_COOKIE_NAME, require_current_user
from app.db import get_session
from app.models.user import AppUser
from app.schemas.user import ErrorResponse, UserResponse
from app.services.guest_accounts import create_guest_account
from app.services.session_tokens import sign_session_token
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["auth"])


def write_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=not settings.is_local,
        samesite="lax",
        path="/",
    )


@router.post("/auth/guest", status_code=status.HTTP_201_CREATED)
async def start_guest_session(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse:
    user = await create_guest_account(session)
    token = sign_session_token(user.id, settings.session_secret, settings.session_ttl_days)
    write_session_cookie(response, token, settings)
    return UserResponse.model_validate(user)


@router.get("/me", responses={401: {"model": ErrorResponse}})
async def read_current_user(user: Annotated[AppUser, Depends(require_current_user)]) -> UserResponse:
    return UserResponse.model_validate(user)
