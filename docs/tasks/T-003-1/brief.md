# Brief T-003-1: Contract + migrations (data foundation)

You are the **orchestrator-grade implementer** for this one task (it sets the schema every other 003 task builds on). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/003-generation-core/spec.md` (AC-1, AC-2, AC-7, AC-8 data parts)
- Design: `docs/specs/003-generation-core/design.md` sections **Data**, **Credit rules and job states**, **Presets catalog**, **ModelAdapter** (types only), **Storage**, **Settings added**, **Test plan** (T-003-1 rows)
- Contract: `packages/contracts/openapi.json` (already published; must not change in this task)
- Patterns: `apps/api/app/models/user.py`, `apps/api/migrations/versions/0001_create_app_user.py`, `apps/api/app/settings.py`, `apps/api/tests/conftest.py`

## Goal
Every table, index, check, setting, domain rule and adapter Protocol from the design exists and is tested, so T-003-2 and T-003-6 can start in parallel without guessing.

## Allowed files (touch nothing else)
- `apps/api/app/settings.py`, `apps/api/pyproject.toml`, `apps/api/uv.lock`, `.env.example`, `docker-compose.yml`
- `apps/api/app/models/{preset,asset,job,job_step,ledger_entry}.py`
- `apps/api/migrations/env.py`, `apps/api/migrations/versions/0002_create_generation_tables.py`, `apps/api/migrations/versions/0003_seed_preset_catalog.py`
- `apps/api/app/domain/{__init__,job_states,credit_rules,preset_catalog}.py`
- `apps/api/app/adapters/{__init__,object_storage,model_adapter,s3_object_storage}.py`, `apps/api/app/storage_dependencies.py`
- `apps/api/tests/conftest.py`, `apps/api/tests/fakes/{__init__,in_memory_object_storage}.py`
- `apps/api/tests/{test_migrations,test_domain_rules,test_s3_object_storage}.py`
- `docs/tasks/T-003-1/report.md`

## What to build
1. **Settings:** every field in design § Settings added; add the env names to `.env.example` (no secret values).
2. **Dependencies:** `uv --directory apps/api add boto3`. In `pyproject.toml` set mypy `files = ["app/services", "app/adapters", "app/domain"]`.
3. **Models** mirroring design § Data exactly (column names, types, FKs, check constraints, partial/unique indexes via `Index(..., postgresql_where=...)`).
4. **Migrations:** `0002_create_generation_tables` (5 tables, every index and check named as in the design) and `0003_seed_preset_catalog` (upsert the 12 rows from `app.domain.preset_catalog`; downgrade deletes them). `migrations/env.py` imports the new models.
5. **Domain:** `job_states.py` (`ALLOWED_TRANSITIONS`, `can_transition`, `statuses_allowed_before`, `TERMINAL_STATUSES`), `credit_rules.py` (`GUEST_GRANT_CREDITS=60`, `VIDEO_CREDIT_COST=20`, `MAX_STEP_ATTEMPTS=2`, `hold_amount`, `release_amount`), `preset_catalog.py` (the 12 `PresetDefinition`s with slug, name, description, category, sort_order and the exact descriptions from the design).
6. **Adapter Protocols:** `object_storage.py` (`ObjectStorage`), `model_adapter.py` (`GenerationRequest`, `GenerationResult`, `GenerationError`, `BackendNotConfiguredError`, `ModelAdapter`), with the exact signatures in the design.
7. **`S3ObjectStorage`** + `storage_dependencies.get_object_storage()` (`lru_cache`) + `object_storage.build_asset_url(storage, key, public_base_url, expires_seconds)`, per design § Storage.
8. **docker-compose:** MinIO healthcheck `["CMD", "mc", "ready", "local"]` and a one-shot `minio-init` service (`minio/mc`, `depends_on: minio: condition: service_healthy`) that creates the `media` bucket with `--ignore-existing`.
9. **Test fixtures** (`conftest.py`), keeping `client_without_database` working:
   - `os.environ.setdefault("GENERATION_BACKEND", "mock")` before any settings import.
   - A session-scoped autouse fixture that runs `alembic upgrade head` once (`subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=<apps/api>, check=True)`), replacing `Base.metadata.create_all`.
   - `session_maker` (engine per test, disposed after), `object_storage` (`InMemoryObjectStorage`), `app` (`create_app()` + `state.session_maker` + `dependency_overrides[get_object_storage]`), `client` (signed out), `guest_client` and `other_guest_client` (each its own `AsyncClient` on the same `app`, already `POST /api/v1/auth/guest`-ed).
   - `InMemoryObjectStorage` implements the Protocol with a `dict[str, bytes]`, upload URLs `memory://{key}`, download URLs `memory://{key}?get`, plus `put_bytes(key, data)` for tests.

## Must reuse
- `app/db.py` (`Base`, `create_database_engine`, `create_session_maker`), the `0001` migration style, the existing `open_client` helper in conftest (extend it, don't fork it).

## Acceptance checks
- [ ] `alembic upgrade head` → `alembic downgrade 0001` → `alembic upgrade head` all succeed (`test_migrations.py` does this through subprocess, then asserts 12 presets and the names `ix_job_step_claimable`, `ix_job_step_lease_expiry`, `uq_job_user_idempotency_key`, `uq_ledger_entry_guest_grant`, `uq_ledger_entry_job_hold`, `uq_ledger_entry_job_resolution` in `pg_indexes`)
- [ ] `test_domain_rules.py`: every allowed and a sample of disallowed transitions; catalog has 12 unique slugs, 3 categories, cost 20
- [ ] `test_s3_object_storage.py` against compose MinIO: presigned PUT (httpx, with `upload_headers`) → `read_object_size` → `download_to_path` → `delete_object` → size is `None`
- [ ] All existing tests still pass; `openapi.json` is byte-identical after `scripts/export-openapi`
- [ ] mypy strict is clean on `app/services`, `app/adapters`, `app/domain`

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db minio && docker compose run --rm minio-init
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
scripts/check-standards
```

## Out of scope
- Repositories, services, router logic, the worker, ffmpeg, SSE (T-003-2…6).
- Any change to `app/schemas/*` or `openapi.json`. If the contract looks wrong, stop and write it in the report.

## Report
Write `docs/tasks/T-003-1/report.md` using `docs/templates/report.md`, then follow the definition of done in `AGENTS.md` (commit per the kickoff prompt, plain message, no trailers, include `.agent-logs/`).
