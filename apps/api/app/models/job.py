import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

JOB_KIND_CHECK = "kind IN ('video', 'image')"
JOB_INPUTS_BY_KIND_CHECK = (
    "(kind = 'video' AND preset_slug IS NOT NULL AND input_asset_id IS NOT NULL)"
    " OR (kind = 'image' AND preset_slug IS NULL AND input_asset_id IS NULL)"
)
JOB_IMAGE_PARAMS_CHECK = (
    "(kind = 'image' AND aspect_ratio IS NOT NULL AND quality IS NOT NULL"
    " AND image_count BETWEEN 1 AND 4)"
    " OR (kind = 'video' AND aspect_ratio IS NULL AND quality IS NULL AND image_count IS NULL)"
)


class Job(Base):
    __tablename__ = "job"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')", name="ck_job_status"
        ),
        CheckConstraint(JOB_KIND_CHECK, name="ck_job_kind"),
        CheckConstraint(JOB_INPUTS_BY_KIND_CHECK, name="ck_job_inputs_by_kind"),
        CheckConstraint(JOB_IMAGE_PARAMS_CHECK, name="ck_job_image_params"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_job_user_idempotency_key"),
        Index("ix_job_user_created", "user_id", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'video'")
    )
    preset_slug: Mapped[str | None] = mapped_column(String(64), ForeignKey("preset.slug"))
    input_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id")
    )
    prompt: Mapped[str | None] = mapped_column(String(500))
    aspect_ratio: Mapped[str | None] = mapped_column(String(8))
    quality: Mapped[str | None] = mapped_column(String(16))
    image_count: Mapped[int | None] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    credit_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    output_video_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id")
    )
    output_poster_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id")
    )
    generated_by: Mapped[str | None] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
