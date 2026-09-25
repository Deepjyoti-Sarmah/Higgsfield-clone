"""sequence jobs"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

OLD_JOB_KIND_CHECK = "kind IN ('video', 'image')"
OLD_JOB_INPUTS_BY_KIND_CHECK = (
    "(kind = 'video' AND preset_slug IS NOT NULL AND input_asset_id IS NOT NULL)"
    " OR (kind = 'image' AND preset_slug IS NULL AND input_asset_id IS NULL)"
)
OLD_JOB_IMAGE_PARAMS_CHECK = (
    "(kind = 'image' AND aspect_ratio IS NOT NULL AND quality IS NOT NULL"
    " AND image_count BETWEEN 1 AND 4)"
    " OR (kind = 'video' AND aspect_ratio IS NULL AND quality IS NULL AND image_count IS NULL)"
)
OLD_ASSET_KIND_CHECK = (
    "kind IN ('input_image', 'output_video', 'output_poster', 'output_image')"
)
JOB_KIND_CHECK = "kind IN ('video', 'image', 'sequence')"
JOB_INPUTS_BY_KIND_CHECK = (
    "(kind = 'video' AND preset_slug IS NOT NULL AND input_asset_id IS NOT NULL)"
    " OR (kind = 'image' AND preset_slug IS NULL AND input_asset_id IS NULL)"
    " OR (kind = 'sequence' AND preset_slug IS NULL AND input_asset_id IS NULL)"
)
JOB_IMAGE_PARAMS_CHECK = (
    "(kind = 'image' AND aspect_ratio IS NOT NULL AND quality IS NOT NULL"
    " AND image_count BETWEEN 1 AND 4)"
    " OR (kind = 'video' AND aspect_ratio IS NULL AND quality IS NULL AND image_count IS NULL)"
    " OR (kind = 'sequence' AND aspect_ratio IS NULL AND quality IS NULL"
    " AND image_count IS NULL)"
)
ASSET_KIND_CHECK = (
    "kind IN ('input_image', 'output_video', 'output_poster', 'output_image', 'input_audio')"
)
JOB_AUDIO_CHECK = "audio_asset_id IS NULL OR kind = 'sequence'"
JOB_DURATION_CHECK = "duration_ms IS NULL OR duration_ms > 0"
CLIP_POSITION_CHECK = "position BETWEEN 0 AND 5"
CLIP_TRANSITION_CHECK = "transition_in IN ('cut', 'crossfade', 'fade_black')"


def upgrade() -> None:
    op.drop_constraint("ck_asset_kind", "asset", type_="check")
    op.create_check_constraint("ck_asset_kind", "asset", ASSET_KIND_CHECK)

    op.drop_constraint("ck_job_kind", "job", type_="check")
    op.drop_constraint("ck_job_inputs_by_kind", "job", type_="check")
    op.drop_constraint("ck_job_image_params", "job", type_="check")
    op.create_check_constraint("ck_job_kind", "job", JOB_KIND_CHECK)
    op.create_check_constraint("ck_job_inputs_by_kind", "job", JOB_INPUTS_BY_KIND_CHECK)
    op.create_check_constraint("ck_job_image_params", "job", JOB_IMAGE_PARAMS_CHECK)

    op.add_column("job", sa.Column("audio_asset_id", UUID(as_uuid=True), sa.ForeignKey("asset.id")))
    op.add_column("job", sa.Column("duration_ms", sa.Integer()))
    op.create_check_constraint("ck_job_audio_sequence_only", "job", JOB_AUDIO_CHECK)
    op.create_check_constraint("ck_job_duration_positive", "job", JOB_DURATION_CHECK)

    op.create_table(
        "job_sequence_clip",
        sa.Column(
            "job_id",
            UUID(as_uuid=True),
            sa.ForeignKey("job.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("source_job_id", UUID(as_uuid=True), sa.ForeignKey("job.id"), nullable=False),
        sa.Column("transition_in", sa.String(16), nullable=False),
        sa.CheckConstraint(CLIP_POSITION_CHECK, name="ck_job_sequence_clip_position"),
        sa.CheckConstraint(CLIP_TRANSITION_CHECK, name="ck_job_sequence_clip_transition"),
        sa.PrimaryKeyConstraint("job_id", "position"),
    )
    op.create_index("ix_job_sequence_clip_source_job", "job_sequence_clip", ["source_job_id"])


def downgrade() -> None:
    op.drop_index("ix_job_sequence_clip_source_job", table_name="job_sequence_clip")
    op.drop_table("job_sequence_clip")
    op.drop_constraint("ck_job_duration_positive", "job", type_="check")
    op.drop_constraint("ck_job_audio_sequence_only", "job", type_="check")
    op.drop_column("job", "duration_ms")
    op.drop_column("job", "audio_asset_id")
    op.drop_constraint("ck_job_image_params", "job", type_="check")
    op.drop_constraint("ck_job_inputs_by_kind", "job", type_="check")
    op.drop_constraint("ck_job_kind", "job", type_="check")
    op.create_check_constraint("ck_job_kind", "job", OLD_JOB_KIND_CHECK)
    op.create_check_constraint("ck_job_inputs_by_kind", "job", OLD_JOB_INPUTS_BY_KIND_CHECK)
    op.create_check_constraint("ck_job_image_params", "job", OLD_JOB_IMAGE_PARAMS_CHECK)
    op.drop_constraint("ck_asset_kind", "asset", type_="check")
    op.create_check_constraint("ck_asset_kind", "asset", OLD_ASSET_KIND_CHECK)
