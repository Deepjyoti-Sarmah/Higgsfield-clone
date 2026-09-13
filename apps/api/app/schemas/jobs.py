import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

JobStatus = Literal["queued", "running", "succeeded", "failed"]


class JobCreateRequest(BaseModel):
    preset_slug: str = Field(min_length=1, max_length=64)
    input_asset_id: uuid.UUID
    prompt: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=100)


class JobCreatedResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int


class JobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    preset_slug: str
    preset_name: str
    prompt: str | None
    credit_cost: int
    input_asset_id: uuid.UUID
    input_image_url: str | None
    video_url: str | None
    poster_url: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class JobStatusEvent(BaseModel):
    job_id: uuid.UUID
    status: JobStatus


class InsufficientCreditsResponse(BaseModel):
    detail: str
    balance: int
    required: int
