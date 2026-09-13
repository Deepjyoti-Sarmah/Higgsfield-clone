"""preset preview keys"""
from alembic import op
from sqlalchemy import bindparam, inspect, text

from app.domain.preset_catalog import PREVIEW_KEYS

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

SET_PREVIEW_KEYS = text(
    "UPDATE preset SET preview_key = :preview_key WHERE slug = :slug"
).bindparams(bindparam("preview_key"), bindparam("slug"))


def _columns() -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns("preset")}


def upgrade() -> None:
    if "preview_key" not in _columns():
        op.alter_column("preset", "preview_url", new_column_name="preview_key")
    connection = op.get_bind()
    for slug, key in PREVIEW_KEYS.items():
        connection.execute(SET_PREVIEW_KEYS, {"slug": slug, "preview_key": key})


def downgrade() -> None:
    columns = _columns()
    if "preview_key" in columns:
        op.execute(text("UPDATE preset SET preview_key = NULL"))
        op.alter_column("preset", "preview_key", new_column_name="preview_url")
