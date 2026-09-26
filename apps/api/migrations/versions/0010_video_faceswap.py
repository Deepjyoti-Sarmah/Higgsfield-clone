"""video target face swap jobs"""
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

OLD_JOB_KIND_CHECK = "kind IN ('video', 'image', 'sequence', 'faceswap')"
OLD_JOB_INPUTS_BY_KIND_CHECK = (
    "(kind = 'video' AND preset_slug IS NOT NULL AND input_asset_id IS NOT NULL)"
    " OR (kind = 'image' AND preset_slug IS NULL AND input_asset_id IS NULL)"
    " OR (kind = 'sequence' AND preset_slug IS NULL AND input_asset_id IS NULL)"
    " OR (kind = 'faceswap' AND preset_slug IS NULL AND input_asset_id IS NULL)"
)
OLD_JOB_IMAGE_PARAMS_CHECK = (
    "(kind = 'image' AND aspect_ratio IS NOT NULL AND quality IS NOT NULL"
    " AND image_count BETWEEN 1 AND 4)"
    " OR (kind = 'video' AND aspect_ratio IS NULL AND quality IS NULL AND image_count IS NULL)"
    " OR (kind = 'sequence' AND aspect_ratio IS NULL AND quality IS NULL"
    " AND image_count IS NULL)"
    " OR (kind = 'faceswap' AND aspect_ratio IS NULL AND quality IS NULL"
    " AND image_count IS NULL)"
)
OLD_JOB_FACESWAP_ASSETS_CHECK = (
    "(kind = 'faceswap' AND face_source_asset_id IS NOT NULL"
    " AND face_target_asset_id IS NOT NULL)"
    " OR (kind != 'faceswap' AND face_source_asset_id IS NULL"
    " AND face_target_asset_id IS NULL)"
)
JOB_KIND_CHECK = "kind IN ('video', 'image', 'sequence', 'faceswap', 'video_faceswap')"
JOB_INPUTS_BY_KIND_CHECK = (
    "(kind = 'video' AND preset_slug IS NOT NULL AND input_asset_id IS NOT NULL)"
    " OR (kind = 'image' AND preset_slug IS NULL AND input_asset_id IS NULL)"
    " OR (kind = 'sequence' AND preset_slug IS NULL AND input_asset_id IS NULL)"
    " OR (kind = 'faceswap' AND preset_slug IS NULL AND input_asset_id IS NULL)"
    " OR (kind = 'video_faceswap' AND preset_slug IS NULL AND input_asset_id IS NULL)"
)
JOB_IMAGE_PARAMS_CHECK = (
    "(kind = 'image' AND aspect_ratio IS NOT NULL AND quality IS NOT NULL"
    " AND image_count BETWEEN 1 AND 4)"
    " OR (kind = 'video' AND aspect_ratio IS NULL AND quality IS NULL AND image_count IS NULL)"
    " OR (kind = 'sequence' AND aspect_ratio IS NULL AND quality IS NULL"
    " AND image_count IS NULL)"
    " OR (kind = 'faceswap' AND aspect_ratio IS NULL AND quality IS NULL"
    " AND image_count IS NULL)"
    " OR (kind = 'video_faceswap' AND aspect_ratio IS NULL AND quality IS NULL"
    " AND image_count IS NULL)"
)
# The video path reuses the face asset columns, so both swap kinds share one check.
JOB_FACESWAP_ASSETS_CHECK = (
    "(kind IN ('faceswap', 'video_faceswap') AND face_source_asset_id IS NOT NULL"
    " AND face_target_asset_id IS NOT NULL)"
    " OR (kind NOT IN ('faceswap', 'video_faceswap') AND face_source_asset_id IS NULL"
    " AND face_target_asset_id IS NULL)"
)


def upgrade() -> None:
    op.drop_constraint("ck_job_kind", "job", type_="check")
    op.drop_constraint("ck_job_inputs_by_kind", "job", type_="check")
    op.drop_constraint("ck_job_image_params", "job", type_="check")
    op.drop_constraint("ck_job_faceswap_assets", "job", type_="check")
    op.create_check_constraint("ck_job_kind", "job", JOB_KIND_CHECK)
    op.create_check_constraint("ck_job_inputs_by_kind", "job", JOB_INPUTS_BY_KIND_CHECK)
    op.create_check_constraint("ck_job_image_params", "job", JOB_IMAGE_PARAMS_CHECK)
    op.create_check_constraint("ck_job_faceswap_assets", "job", JOB_FACESWAP_ASSETS_CHECK)


def downgrade() -> None:
    op.drop_constraint("ck_job_faceswap_assets", "job", type_="check")
    op.drop_constraint("ck_job_image_params", "job", type_="check")
    op.drop_constraint("ck_job_inputs_by_kind", "job", type_="check")
    op.drop_constraint("ck_job_kind", "job", type_="check")
    op.create_check_constraint("ck_job_kind", "job", OLD_JOB_KIND_CHECK)
    op.create_check_constraint("ck_job_inputs_by_kind", "job", OLD_JOB_INPUTS_BY_KIND_CHECK)
    op.create_check_constraint("ck_job_image_params", "job", OLD_JOB_IMAGE_PARAMS_CHECK)
    op.create_check_constraint("ck_job_faceswap_assets", "job", OLD_JOB_FACESWAP_ASSETS_CHECK)
