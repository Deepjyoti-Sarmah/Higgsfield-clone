import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_guest: bool
    display_name: str | None
    created_at: datetime


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "down"]


class ErrorResponse(BaseModel):
    detail: str
