import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.jobs import JobStatus


class PublicJobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    preset_slug: str
    preset_name: str
    poster_url: str | None
    video_url: str | None
    created_at: datetime
