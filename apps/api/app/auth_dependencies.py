from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import AppUser
from app.services.guest_accounts import find_account
from app.services.session_tokens import read_session_user_id
from app.settings import Settings, get_settings

SESSION_COOKIE_NAME = "session"


async def require_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> AppUser:
    user_id = read_session_user_id(session_cookie, settings.session_secret) if session_cookie else None
    user = await find_account(session, user_id) if user_id else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return user
