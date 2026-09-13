"""guardrails: guest issuance + job.generated_by"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job", sa.Column("generated_by", sa.String(32)))
    op.create_table(
        "guest_issuance",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("ip_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_guest_issuance_ip_created", "guest_issuance", ["ip_hash", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_guest_issuance_ip_created", table_name="guest_issuance")
    op.drop_table("guest_issuance")
    op.drop_column("job", "generated_by")
