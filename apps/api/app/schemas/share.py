import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.jobs import JobKind, JobStatus


class PublicJobResponse(BaseModel):
    id: uuid.UUID
    kind: JobKind = "video"
    status: JobStatus
    preset_slug: str | None
    preset_name: str | None
    poster_url: str | None
    video_url: str | None
    image_urls: list[str] = []
    clip_count: int | None = None
    duration_ms: int | None = None
    created_at: datetime
