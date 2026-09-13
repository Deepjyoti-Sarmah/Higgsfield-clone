"""image jobs"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

OLD_ASSET_KIND_CHECK = "kind IN ('input_image', 'output_video', 'output_poster')"
ASSET_KIND_CHECK = "kind IN ('input_image', 'output_video', 'output_poster', 'output_image')"
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


def upgrade() -> None:
    op.drop_constraint("ck_asset_kind", "asset", type_="check")
    op.create_check_constraint("ck_asset_kind", "asset", ASSET_KIND_CHECK)

    op.add_column(
        "job", sa.Column("kind", sa.String(16), nullable=False, server_default=sa.text("'video'"))
    )
    op.add_column("job", sa.Column("aspect_ratio", sa.String(8)))
    op.add_column("job", sa.Column("quality", sa.String(16)))
    op.add_column("job", sa.Column("image_count", sa.Integer()))
    op.alter_column("job", "preset_slug", existing_type=sa.String(64), nullable=True)
    op.alter_column("job", "input_asset_id", existing_type=UUID(as_uuid=True), nullable=True)
    op.create_check_constraint("ck_job_kind", "job", JOB_KIND_CHECK)
    op.create_check_constraint("ck_job_inputs_by_kind", "job", JOB_INPUTS_BY_KIND_CHECK)
    op.create_check_constraint("ck_job_image_params", "job", JOB_IMAGE_PARAMS_CHECK)

    op.create_table(
        "job_image",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "job_id",
            UUID(as_uuid=True),
            sa.ForeignKey("job.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("asset.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("job_id", "position", name="uq_job_image_position"),
        sa.UniqueConstraint("asset_id", name="uq_job_image_asset"),
    )


def downgrade() -> None:
    op.drop_table("job_image")
    op.drop_constraint("ck_job_image_params", "job", type_="check")
    op.drop_constraint("ck_job_inputs_by_kind", "job", type_="check")
    op.drop_constraint("ck_job_kind", "job", type_="check")
    op.alter_column("job", "input_asset_id", existing_type=UUID(as_uuid=True), nullable=False)
    op.alter_column("job", "preset_slug", existing_type=sa.String(64), nullable=False)
    op.drop_column("job", "image_count")
    op.drop_column("job", "quality")
    op.drop_column("job", "aspect_ratio")
    op.drop_column("job", "kind")
    op.drop_constraint("ck_asset_kind", "asset", type_="check")
    op.create_check_constraint("ck_asset_kind", "asset", OLD_ASSET_KIND_CHECK)
