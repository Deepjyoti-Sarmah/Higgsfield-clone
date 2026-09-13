import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.image_rules import MAX_IMAGE_COUNT, ImageAspectRatio, ImageQuality
from app.schemas.jobs import JobStatus


class ImageJobCreateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    aspect_ratio: ImageAspectRatio
    quality: ImageQuality
    count: int = Field(ge=1, le=MAX_IMAGE_COUNT)
    idempotency_key: str = Field(min_length=8, max_length=100)


class ImageJobCreatedResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int
    image_count: int


class ImageJobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    prompt: str
    aspect_ratio: ImageAspectRatio
    quality: ImageQuality
    count: int
    credit_cost: int
    backend: str | None
    image_urls: list[str]
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class ImageCreditCosts(BaseModel):
    standard: int
    high: int


class ImageOptionsResponse(BaseModel):
    aspect_ratios: list[ImageAspectRatio]
    qualities: list[ImageQuality]
    max_count: int
    credit_costs: ImageCreditCosts
