from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_dependencies import require_current_user
from app.db import get_session
from app.models.user import AppUser
from app.schemas.credits import CreditsResponse, TopUpResponse
from app.schemas.user import ErrorResponse
from app.services.credits import grant_top_up_credits, read_balance

router = APIRouter(prefix="/api/v1", tags=["credits"])


@router.get("/credits", responses={401: {"model": ErrorResponse}})
async def read_credits(
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreditsResponse:
    return CreditsResponse(balance=await read_balance(session, user.id))


@router.post(
    "/credits/topup",
    response_model=TopUpResponse,
    responses={401: {"model": ErrorResponse}},
)
async def top_up_credits(
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TopUpResponse:
    result = await grant_top_up_credits(session, user.id)
    return TopUpResponse(amount=result.amount, balance=result.balance)
