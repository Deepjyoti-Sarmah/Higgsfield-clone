"""seed preset catalog"""
from alembic import op
from sqlalchemy import text

from app.domain.preset_catalog import PRESET_CATALOG

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

UPSERT_PRESET = text(
    """
    INSERT INTO preset (slug, name, description, category, credit_cost, sort_order, is_active)
    VALUES (:slug, :name, :description, :category, :credit_cost, :sort_order, true)
    ON CONFLICT (slug) DO UPDATE SET
        name = EXCLUDED.name,
        description = EXCLUDED.description,
        category = EXCLUDED.category,
        credit_cost = EXCLUDED.credit_cost,
        sort_order = EXCLUDED.sort_order,
        is_active = true
    """
)


def upgrade() -> None:
    connection = op.get_bind()
    for preset in PRESET_CATALOG:
        connection.execute(
            UPSERT_PRESET,
            {
                "slug": preset.slug,
                "name": preset.name,
                "description": preset.description,
                "category": preset.category,
                "credit_cost": preset.credit_cost,
                "sort_order": preset.sort_order,
            },
        )


def downgrade() -> None:
    connection = op.get_bind()
    for preset in PRESET_CATALOG:
        connection.execute(text("DELETE FROM preset WHERE slug = :slug"), {"slug": preset.slug})
