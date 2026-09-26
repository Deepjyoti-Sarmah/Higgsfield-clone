import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.jobs import JobStatus


class VideoFaceSwapJobCreateRequest(BaseModel):
    source_asset_id: uuid.UUID
    target_asset_id: uuid.UUID | None = None
    target_job_id: uuid.UUID | None = None
    keyframe_asset_id: uuid.UUID | None = None
    idempotency_key: str = Field(min_length=8, max_length=100)

    @model_validator(mode="after")
    def _exactly_one_target(self) -> "VideoFaceSwapJobCreateRequest":
        if (self.target_asset_id is None) == (self.target_job_id is None):
            raise ValueError("exactly one of target_asset_id, target_job_id is required")
        return self


class VideoFaceSwapJobCreatedResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int


class VideoFaceSwapJobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int
    source_url: str | None
    target_url: str | None
    video_url: str | None
    poster_url: str | None
    duration_ms: int | None
    generated_by: str | None
    error_message: str | None
    created_at: datetime
