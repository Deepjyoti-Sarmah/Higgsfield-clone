"""create generation tables"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

STATUS_CHECK = "status IN ('queued', 'running', 'succeeded', 'failed')"
AMOUNT_SIGN_CHECK = (
    "(kind = 'HOLD' AND amount < 0) OR (kind = 'SETTLE' AND amount = 0)"
    " OR (kind IN ('GRANT', 'TOPUP', 'RELEASE') AND amount > 0)"
)
JOB_LINK_CHECK = "(kind IN ('HOLD', 'SETTLE', 'RELEASE')) = (job_id IS NOT NULL)"


def create_preset_table() -> None:
    op.create_table(
        "preset",
        sa.Column("slug", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("credit_cost", sa.Integer(), nullable=False),
        sa.Column("preview_url", sa.Text()),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("category IN ('camera', 'cinematic', 'dynamic')", name="ck_preset_category"),
        sa.CheckConstraint("credit_cost > 0", name="ck_preset_credit_cost"),
    )


def create_asset_table() -> None:
    op.create_table(
        "asset",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.BigInteger()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('input_image', 'output_video', 'output_poster')", name="ck_asset_kind"),
        sa.CheckConstraint("status IN ('pending', 'ready')", name="ck_asset_status"),
        sa.UniqueConstraint("storage_key", name="uq_asset_storage_key"),
    )
    op.create_index("ix_asset_user_created", "asset", ["user_id", sa.text("created_at DESC")])


def create_job_table() -> None:
    op.create_table(
        "job",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("preset_slug", sa.String(64), sa.ForeignKey("preset.slug"), nullable=False),
        sa.Column("input_asset_id", UUID(as_uuid=True), sa.ForeignKey("asset.id"), nullable=False),
        sa.Column("prompt", sa.String(500)),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("credit_cost", sa.Integer(), nullable=False),
        sa.Column("output_video_asset_id", UUID(as_uuid=True), sa.ForeignKey("asset.id")),
        sa.Column("output_poster_asset_id", UUID(as_uuid=True), sa.ForeignKey("asset.id")),
        sa.Column("error_message", sa.String(300)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(STATUS_CHECK, name="ck_job_status"),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_job_user_idempotency_key"),
    )
    op.create_index("ix_job_user_created", "job", ["user_id", sa.text("created_at DESC")])


def create_job_step_table() -> None:
    op.create_table(
        "job_step",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("lease_owner", sa.String(100)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("backend", sa.String(32)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(STATUS_CHECK, name="ck_job_step_status"),
        sa.UniqueConstraint("job_id", "kind", name="uq_job_step_job_kind"),
    )
    op.create_index(
        "ix_job_step_claimable", "job_step", ["created_at"], postgresql_where=sa.text("status = 'queued'")
    )
    op.create_index(
        "ix_job_step_lease_expiry",
        "job_step",
        ["lease_expires_at"],
        postgresql_where=sa.text("status = 'running'"),
    )


def create_ledger_entry_table() -> None:
    op.create_table(
        "ledger_entry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "kind IN ('GRANT', 'HOLD', 'SETTLE', 'RELEASE', 'TOPUP')", name="ck_ledger_entry_kind"
        ),
        sa.CheckConstraint(AMOUNT_SIGN_CHECK, name="ck_ledger_entry_amount_sign"),
        sa.CheckConstraint(JOB_LINK_CHECK, name="ck_ledger_entry_job_link"),
    )
    op.create_index(
        "uq_ledger_entry_guest_grant",
        "ledger_entry",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'GRANT'"),
    )
    op.create_index(
        "uq_ledger_entry_job_hold",
        "ledger_entry",
        ["job_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'HOLD'"),
    )
    op.create_index(
        "uq_ledger_entry_job_resolution",
        "ledger_entry",
        ["job_id"],
        unique=True,
        postgresql_where=sa.text("kind IN ('SETTLE', 'RELEASE')"),
    )
    op.create_index("ix_ledger_entry_user", "ledger_entry", ["user_id"])


def upgrade() -> None:
    create_preset_table()
    create_asset_table()
    create_job_table()
    create_job_step_table()
    create_ledger_entry_table()


def downgrade() -> None:
    op.drop_table("ledger_entry")
    op.drop_table("job_step")
    op.drop_table("job")
    op.drop_table("asset")
    op.drop_table("preset")
