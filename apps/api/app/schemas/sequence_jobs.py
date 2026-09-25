import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.jobs import JobStatus

SequenceTransition = Literal["cut", "crossfade", "fade_black"]


class SequenceClipIn(BaseModel):
    job_id: uuid.UUID
    transition_in: SequenceTransition = "cut"  # ignored for clips[0]; stored as "cut"


class SequenceJobCreateRequest(BaseModel):
    clips: list[SequenceClipIn] = Field(min_length=2, max_length=6)
    audio_asset_id: uuid.UUID | None = None
    idempotency_key: str = Field(min_length=8, max_length=100)


class SequenceJobCreatedResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int
    clip_count: int


class SequenceClipResponse(BaseModel):
    position: int
    job_id: uuid.UUID
    transition_in: SequenceTransition
    thumbnail_url: str | None


class SequenceJobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int
    clips: list[SequenceClipResponse]
    has_audio: bool
    video_url: str | None
    poster_url: str | None
    duration_ms: int | None
    generated_by: str | None
    error_message: str | None
    created_at: datetime
