import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

AMOUNT_SIGN_CHECK = (
    "(kind = 'HOLD' AND amount < 0) OR (kind = 'SETTLE' AND amount = 0)"
    " OR (kind IN ('GRANT', 'TOPUP', 'RELEASE') AND amount > 0)"
)
JOB_LINK_CHECK = "(kind IN ('HOLD', 'SETTLE', 'RELEASE')) = (job_id IS NOT NULL)"


class LedgerEntry(Base):
    __tablename__ = "ledger_entry"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('GRANT', 'HOLD', 'SETTLE', 'RELEASE', 'TOPUP')", name="ck_ledger_entry_kind"
        ),
        CheckConstraint(AMOUNT_SIGN_CHECK, name="ck_ledger_entry_amount_sign"),
        CheckConstraint(JOB_LINK_CHECK, name="ck_ledger_entry_job_link"),
        Index(
            "uq_ledger_entry_guest_grant",
            "user_id",
            unique=True,
            postgresql_where=text("kind = 'GRANT'"),
        ),
        Index(
            "uq_ledger_entry_job_hold",
            "job_id",
            unique=True,
            postgresql_where=text("kind = 'HOLD'"),
        ),
        Index(
            "uq_ledger_entry_job_resolution",
            "job_id",
            unique=True,
            postgresql_where=text("kind IN ('SETTLE', 'RELEASE')"),
        ),
        Index("ix_ledger_entry_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
