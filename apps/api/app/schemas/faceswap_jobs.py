import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.jobs import JobStatus


class FaceSwapJobCreateRequest(BaseModel):
    source_asset_id: uuid.UUID
    target_asset_id: uuid.UUID
    idempotency_key: str = Field(min_length=8, max_length=100)


class FaceSwapJobCreatedResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int


class FaceSwapJobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int
    source_url: str | None
    target_url: str | None
    image_url: str | None
    generated_by: str | None
    error_message: str | None
    created_at: datetime
