from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_dependencies import SESSION_COOKIE_NAME, require_current_user
from app.db import get_session
from app.models.user import AppUser
from app.schemas.jobs import LimitExceededResponse
from app.schemas.user import ErrorResponse, UserResponse
from app.services.guardrails import GuestLimitError, client_ip, hash_client_ip
from app.services.guest_accounts import create_guest_account
from app.services.session_tokens import sign_session_token
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["auth"])

GUEST_LIMIT_DETAIL = "Too many guest sessions from this address today."


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


@router.post("/auth/guest", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def start_guest_session(
    response: Response,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse | JSONResponse:
    ip_hash = hash_client_ip(client_ip(request), settings.session_secret)
    try:
        user = await create_guest_account(session, ip_hash=ip_hash)
    except GuestLimitError as error:
        body = LimitExceededResponse(detail=GUEST_LIMIT_DETAIL, limit=error.limit, used=error.used)
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body.model_dump())
    token = sign_session_token(user.id, settings.session_secret, settings.session_ttl_days)
    write_session_cookie(response, token, settings)
    return UserResponse.model_validate(user)


@router.get("/me", responses={401: {"model": ErrorResponse}})
async def read_current_user(user: Annotated[AppUser, Depends(require_current_user)]) -> UserResponse:
    return UserResponse.model_validate(user)
