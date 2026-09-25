import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class JobSequenceClip(Base):
    __tablename__ = "job_sequence_clip"
    __table_args__ = (
        CheckConstraint("position BETWEEN 0 AND 5", name="ck_job_sequence_clip_position"),
        CheckConstraint(
            "transition_in IN ('cut', 'crossfade', 'fade_black')",
            name="ck_job_sequence_clip_transition",
        ),
        Index("ix_job_sequence_clip_source_job", "source_job_id"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    source_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job.id"), nullable=False
    )
    transition_in: Mapped[str] = mapped_column(String(16), nullable=False)
