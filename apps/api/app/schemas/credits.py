import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CreditsResponse(BaseModel):
    balance: int


class TopUpResponse(BaseModel):
    amount: int
    balance: int


LedgerKind = Literal["GRANT", "HOLD", "SETTLE", "RELEASE", "TOPUP"]


class LedgerEntryResponse(BaseModel):
    id: uuid.UUID
    kind: LedgerKind
    amount: int
    job_id: uuid.UUID | None
    created_at: datetime


class LedgerListResponse(BaseModel):
    items: list[LedgerEntryResponse]
