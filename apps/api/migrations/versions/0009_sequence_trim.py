"""sequence clip trim"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_sequence_clip",
        sa.Column("trim_start_ms", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "job_sequence_clip", sa.Column("trim_end_ms", sa.Integer(), nullable=True)
    )
    op.create_check_constraint(
        "ck_job_sequence_clip_trim",
        "job_sequence_clip",
        "trim_end_ms IS NULL OR trim_end_ms > trim_start_ms",
    )


def downgrade() -> None:
    op.drop_constraint("ck_job_sequence_clip_trim", "job_sequence_clip", type_="check")
    op.drop_column("job_sequence_clip", "trim_end_ms")
    op.drop_column("job_sequence_clip", "trim_start_ms")
