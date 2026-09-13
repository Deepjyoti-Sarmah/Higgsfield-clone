import subprocess
import sys
from pathlib import Path

from sqlalchemy import TextClause, bindparam, text

from app.db import create_database_engine
from app.settings import get_settings

API_DIR = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {"preset", "asset", "job", "job_step", "ledger_entry"}
EXPECTED_INDEXES = {
    "ix_job_step_claimable",
    "ix_job_step_lease_expiry",
    "uq_job_user_idempotency_key",
    "uq_ledger_entry_guest_grant",
    "uq_ledger_entry_job_hold",
    "uq_ledger_entry_job_resolution",
}


def run_alembic(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=API_DIR, check=True)


def catalog_names_query(catalog: str, table: str) -> TextClause:
    return text(
        f"SELECT {catalog} FROM {table} WHERE schemaname = 'public' AND {catalog} IN :names"
    ).bindparams(bindparam("names", expanding=True))


async def test_upgrade_downgrade_upgrade_seeds_catalog_and_creates_indexes() -> None:
    run_alembic("upgrade", "head")
    run_alembic("downgrade", "0001")

    engine = create_database_engine(get_settings())
    async with engine.connect() as connection:
        assert await connection.scalar(text("SELECT to_regclass('public.preset')")) is None

    run_alembic("upgrade", "head")

    async with engine.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM preset")) == 12
        found_indexes = set(
            (
                await connection.execute(
                    catalog_names_query("indexname", "pg_indexes"),
                    {"names": sorted(EXPECTED_INDEXES)},
                )
            ).scalars()
        )
        found_tables = set(
            (
                await connection.execute(
                    catalog_names_query("tablename", "pg_tables"),
                    {"names": sorted(EXPECTED_TABLES)},
                )
            ).scalars()
        )
    await engine.dispose()

    assert found_indexes == EXPECTED_INDEXES
    assert found_tables == EXPECTED_TABLES
