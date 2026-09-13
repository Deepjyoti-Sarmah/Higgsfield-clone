import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

UploadContentType = Literal["image/jpeg", "image/png", "image/webp"]
AssetKind = Literal["input_image", "output_video", "output_poster"]
AssetStatus = Literal["pending", "ready"]


class UploadCreateRequest(BaseModel):
    content_type: UploadContentType
    byte_size: int = Field(gt=0, le=MAX_UPLOAD_BYTES)


class UploadCreateResponse(BaseModel):
    asset_id: uuid.UUID
    upload_url: str
    upload_method: Literal["PUT"] = "PUT"
    # The browser must send exactly these headers on the PUT, or the presigned signature fails.
    upload_headers: dict[str, str]
    expires_at: datetime


class AssetResponse(BaseModel):
    id: uuid.UUID
    kind: AssetKind
    status: AssetStatus
    content_type: str
    byte_size: int | None
    url: str | None
