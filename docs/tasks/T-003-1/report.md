# Report T-003-1

**Agent / model / tool:** implementer (subagent) · DeepSeek (deepseek-flash) · DeepSeek Harness
**Result:** DONE

## Files changed
- `apps/api/app/settings.py`: added the 17 design § Settings fields (`generation_backend` … `paid_budget_cents`) and the `GenerationBackend` literal.
- `apps/api/pyproject.toml`: added `boto3>=1.43.93`; mypy `files = ["app/services", "app/adapters", "app/domain"]`.
- `apps/api/uv.lock`: boto3/botocore/s3transfer/jmespath/urllib3 resolution from `uv add`.
- `.env.example`: added the env names `S3_REGION`, `UPLOAD_URL_TTL_SECONDS`, `DOWNLOAD_URL_TTL_SECONDS`, `GENERATION_TIMEOUT_SECONDS`, `MOCK_GENERATION_FAILS`, `MODAL_ENDPOINT_URL`, `WORKER_LEASE_SECONDS`, `WORKER_POLL_SECONDS`, `WORKER_REAPER_SECONDS` (no values/secrets).
- `docker-compose.yml`: MinIO `healthcheck: ["CMD","mc","ready","local"]`; one-shot `minio-init` service (`depends_on: minio: condition: service_healthy`) that sets an `mc` alias and runs `mc mb --ignore-existing local/media` + `mc anonymous set none local/media`.
- `apps/api/app/models/preset.py`, `asset.py`, `job.py`, `job_step.py`, `ledger_entry.py`: the 5 mapped classes mirroring design § Data (columns, types, FKs, checks, unique/partial indexes).
- `apps/api/migrations/env.py`: imports all 6 model modules so `Base.metadata` is complete.
- `apps/api/migrations/versions/0002_create_generation_tables.py`: 5 tables + all named indexes/checks; downgrade drops them.
- `apps/api/migrations/versions/0003_seed_preset_catalog.py`: `INSERT … ON CONFLICT (slug) DO UPDATE` for the 12 `PRESET_CATALOG` rows; downgrade deletes those slugs.
- `apps/api/app/domain/__init__.py`, `job_states.py` (`ALLOWED_TRANSITIONS`, `can_transition`, `statuses_allowed_before`, `TERMINAL_STATUSES`), `credit_rules.py` (`GUEST_GRANT_CREDITS=60`, `VIDEO_CREDIT_COST=20`, `MAX_STEP_ATTEMPTS=2`, `LedgerKind`, `hold_amount`, `release_amount`), `preset_catalog.py` (12 `PresetDefinition`s, exact design descriptions).
- `apps/api/app/adapters/__init__.py`, `object_storage.py` (`ObjectStorage` Protocol + `build_asset_url`), `model_adapter.py` (`GenerationRequest`, `GenerationResult`, `GenerationError`, `BackendNotConfiguredError`, `ModelAdapter`), `s3_object_storage.py` (`S3ObjectStorage` via boto3, presign + `asyncio.to_thread` network calls).
- `apps/api/app/storage_dependencies.py`: `lru_cache`d `get_object_storage()`.
- `apps/api/tests/conftest.py`: env-before-settings, session-scoped autouse `alembic upgrade head` (no more `Base.metadata.create_all`), `session_maker`, `object_storage`, `app`, `client`, `guest_client`, `other_guest_client`, and a still-working `client_without_database`; `open_client` extended to build an `AsyncClient` from an app.
- `apps/api/tests/fakes/__init__.py`, `in_memory_object_storage.py`: `InMemoryObjectStorage` Protocol double (`memory://{key}`, `memory://{key}?get`, `put_bytes`).
- `apps/api/tests/test_migrations.py`: `upgrade head → downgrade 0001 → upgrade head` via subprocess + 12 presets + the 6 required index names + all 5 tables.
- `apps/api/tests/test_domain_rules.py`: every allowed transition, sample of disallowed ones, `statuses_allowed_before`, terminal set, 12 unique slugs / 3 categories / cost 20, credit helpers.
- `apps/api/tests/test_s3_object_storage.py`: presigned PUT (httpx, signed `Content-Type`) → `read_object_size` → `download_to_path` → `delete_object` → size `None`; a 403 when the PUT sends the wrong content type; `build_asset_url` both branches.
- `docs/tasks/T-003-1/report.md`: this file.

Nothing outside the brief's Allowed files was edited. `packages/contracts/openapi.json` was rewritten by `scripts/export-openapi` and stayed byte-identical (`git diff --exit-code` passed). `docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md`, `apps/api/app/schemas/*`, `.agent-logs/` and commits were left to the orchestrator per the kickoff hard rules.

## Reused
- `app/db.py`: `Base`, `create_database_engine`, `create_session_maker` (no new engine/session code).
- `apps/api/migrations/versions/0001_create_app_user.py`: migration style (`revision`/`down_revision` strings, `op.create_table`, `sa.text("gen_random_uuid()")`).
- `apps/api/tests/conftest.py::open_client`: extended to take the `app` fixture instead of forking a second helper.
- `app/settings.py::get_settings` `lru_cache` pattern copied by `get_object_storage`.
- `tests/fakes/in_memory_object_storage.py` implements the same `ObjectStorage` Protocol used by the API/worker.
- Schemas already frozen by T-003-0 (`app/schemas/{presets,uploads,jobs,credits}.py`) were read, not touched.

## Verify output (full paste, no summarising)
```
$ docker compose up -d --wait db minio && docker compose run --rm minio-init
 Container higgsfield-minio-1 Running 
 Container higgsfield-db-1 Running 
 Container higgsfield-minio-1 Waiting 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-minio-1 Healthy 
 Container higgsfield-db-1 Healthy 
 Container higgsfield-minio-1 Running 
 Container higgsfield-minio-1 Waiting 
 Container higgsfield-minio-1 Healthy 
 Container higgsfield-minio-init-run-337f44d4eb4a Creating 
 Container higgsfield-minio-init-run-337f44d4eb4a Created 
Added `local` successfully.
Bucket created successfully `local/media`.
Access permission for `local/media` is set to `private`
$ uv --directory apps/api run alembic upgrade head
$ uv --directory apps/api run ruff check .
All checks passed!
$ uv --directory apps/api run mypy
Success: no issues found in 12 source files
$ uv --directory apps/api run pytest -q
...................                                                      [100%]
19 passed in 2.66s
$ scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
wrote packages/contracts/openapi.json
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Standards check
```
check-standards: ok (0 violations)
```
(`ruff check .` → `All checks passed!`; `mypy` strict → `Success: no issues found in 12 source files`.)

## Open issues / guesses / things skipped
- **`minio/mc` image is not pullable here.** `docker compose run minio-init` failed with `pull access denied for minio/mc, repository does not exist`. The compose service therefore uses `quay.io/minio/mc:latest` (same publisher/registry as the `quay.io/minio/minio` server image already in the file) instead of the design's literal `minio/mc`. Behavior is identical; only the registry path differs. This is the one deliberate deviation from design § Storage.
- `PresetDefinition` declares `sort_order` before `credit_cost` (with `credit_cost=VIDEO_CREDIT_COST` last). The design wrote `(slug, name, description, category, credit_cost=…, sort_order)`, which is an invalid dataclass (non-default field after a defaulted one); only the field order changed, the constructor values in the catalog are positional and match the design exactly.
- `.env.example` keeps the pre-existing `GENERATION_BACKEND=mock` (safe for tests); the settings default remains `local-motion` per design. No `.env.local` file exists in the repo, so the conftest `setdefault("GENERATION_BACKEND", "mock")` is what tests use.
- `client_without_database` still points at an unreachable DB and disposes its own engine, but now builds its own `create_app()` because `open_client` takes an app. Its behavior (health → 503) is unchanged and covered by `test_health.py`.
- Check-constraint names for the unnamed design checks were chosen consistently: `ck_preset_category`, `ck_preset_credit_cost`, `ck_asset_kind`, `ck_asset_status`, `ck_job_status`, `ck_job_step_status`, `ck_ledger_entry_kind` (the two the design names explicitly — `ck_ledger_entry_amount_sign`, `ck_ledger_entry_job_link` — match verbatim).
- `test_migrations` drops/recreates the 5 tables (downgrade to 0001). The suite is sequential and the three new test files do not depend on rows created by other tests, so this is safe; it is also why the dev DB ends at `0003`/12 presets after the run.
- Ignored (not written): the AGENTS.md definition-of-done items about ticking `tasks.md`, updating `PLAN.md`/`STATUS.md`/`WORKLOG.md`, committing, and including `.agent-logs/` — the kickoff hard rules assign those to the orchestrator.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Generation-core data foundation: settings, 5 models, migrations `0002`/`0003` (12 presets seeded), job-state + credit-rule + preset-catalog domain, `ObjectStorage`/`ModelAdapter` Protocols, `S3ObjectStorage`, MinIO compose + bucket init, conftest fixtures | `apps/api/app/{settings,models/*,domain/*,adapters/*,storage_dependencies}.py`, `apps/api/migrations/versions/000{2,3}_*.py`, `apps/api/tests/{conftest,test_migrations,test_domain_rules,test_s3_object_storage}.py`, `docker-compose.yml` | `docker compose up -d --wait db minio && docker compose run --rm minio-init && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q` → 19 passed; `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` clean; `scripts/check-standards` ok | 2026-09-13 08:35 |
