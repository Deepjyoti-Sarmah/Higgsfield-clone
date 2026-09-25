from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_dependencies import require_current_user
from app.db import get_session
from app.models.user import AppUser
from app.schemas.credits import CreditsResponse, LedgerListResponse, TopUpResponse
from app.schemas.jobs import LimitExceededResponse
from app.schemas.user import ErrorResponse
from app.services.credits import grant_top_up_credits, read_balance, read_ledger
from app.services.guardrails import TopUpLimitError

router = APIRouter(prefix="/api/v1", tags=["credits"])

TOPUP_LIMIT_DETAIL = "Daily top-up limit reached. Try again tomorrow."


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
) -> TopUpResponse | JSONResponse:
    try:
        result = await grant_top_up_credits(session, user.id)
    except TopUpLimitError as error:
        body = LimitExceededResponse(detail=TOPUP_LIMIT_DETAIL, limit=error.limit, used=error.used)
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body.model_dump())
    return TopUpResponse(amount=result.amount, balance=result.balance)


@router.get(
    "/credits/ledger",
    response_model=LedgerListResponse,
    responses={401: {"model": ErrorResponse}},
)
async def read_credit_ledger(
    user: Annotated[AppUser, Depends(require_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> LedgerListResponse:
    return await read_ledger(session, user.id, limit)
