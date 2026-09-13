# Tasks 003: Generation core

Rules:
- One task = one agent run.
- No two tasks share a file (checked in T-003-0; the schemas files are frozen and owned by nobody).
- Every task has a verify command. The full commands are in each brief.

**Waves:** T-003-1 → (T-003-2 ∥ T-003-6) → (T-003-3 ∥ T-003-4 ∥ T-003-5) → T-003-7.

- [x] **T-003-0** · Design + publish the contract (schemas, 501 routers, openapi.json, this file, briefs)
  - Files: `docs/specs/003-generation-core/**`, `docs/tasks/T-003-*/**`, `apps/api/app/schemas/{presets,uploads,jobs,credits}.py`, `apps/api/app/routers/{presets,uploads,jobs,credits}.py`, `apps/api/app/main.py`, `packages/contracts/openapi.json`
  - Verify: see `docs/tasks/T-003-0/brief.md`
  - Suggested role: designer (strongest model) · Depends on: —
- [ ] **T-003-1** · Contract + migrations: settings, models, migrations 0002/0003, domain rules + preset catalog, storage + model Protocols, S3 adapter, test fixtures
  - Files: `apps/api/app/settings.py`, `apps/api/pyproject.toml`, `apps/api/uv.lock`, `.env.example`, `docker-compose.yml`, `apps/api/app/models/{preset,asset,job,job_step,ledger_entry}.py`, `apps/api/migrations/env.py`, `apps/api/migrations/versions/{0002_create_generation_tables,0003_seed_preset_catalog}.py`, `apps/api/app/domain/{__init__,job_states,credit_rules,preset_catalog}.py`, `apps/api/app/adapters/{__init__,object_storage,model_adapter,s3_object_storage}.py`, `apps/api/app/storage_dependencies.py`, `apps/api/tests/conftest.py`, `apps/api/tests/fakes/{__init__,in_memory_object_storage}.py`, `apps/api/tests/{test_migrations,test_domain_rules,test_s3_object_storage}.py`
  - Verify: `docker compose up -d --wait db minio && docker compose run --rm minio-init && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: orchestrator · Depends on: T-003-0
- [ ] **T-003-2** · Repositories: presets, assets, ledger, jobs (+ NOTIFY), job_steps (claim SQL, lease, reaper SQL), user row lock
  - Files: `apps/api/app/repositories/{presets,assets,ledger,jobs,job_steps}.py`, `apps/api/app/repositories/users.py`, `apps/api/tests/{test_job_step_repository,test_ledger_repository}.py`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/check-standards`
  - Suggested role: orchestrator (claim/lease SQL) · Depends on: T-003-1
- [ ] **T-003-3** · Presets, uploads and credits endpoints + the 60-credit guest grant
  - Files: `apps/api/app/services/{presets,uploads,credits}.py`, `apps/api/app/services/guest_accounts.py`, `apps/api/app/routers/{presets,uploads,credits}.py`, `apps/api/tests/{test_presets_api,test_uploads_api,test_credits_api}.py`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-003-2
- [ ] **T-003-4** · Jobs API: create (one transaction, idempotent, 402), read, SSE events (LISTEN broker + stream)
  - Files: `apps/api/app/services/{job_creation,job_views,job_event_broker,job_event_stream}.py`, `apps/api/app/job_event_dependencies.py`, `apps/api/app/routers/jobs.py`, `apps/api/app/main.py`, `apps/api/tests/{test_job_creation_api,test_job_reading_api,test_job_events_api}.py`
  - Verify: same as T-003-3
  - Suggested role: orchestrator (SSE fan-out) · Depends on: T-003-2
- [ ] **T-003-5** · Worker: claim loop, lease renewal, success/failure completion, reaper
  - Files: `apps/api/app/worker.py`, `apps/api/app/services/{step_claiming,generation_runs,step_completion,lease_reaper}.py`, `apps/api/tests/fakes/scripted_model_adapter.py`, `apps/api/tests/{test_step_claiming,test_step_completion,test_lease_reaper}.py`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && (cd apps/api && GENERATION_BACKEND=mock timeout 6 uv run python -m app.worker; test $? -eq 124) && scripts/check-standards`
  - Suggested role: orchestrator (claim/lease core) · Depends on: T-003-2, T-003-6
- [ ] **T-003-6** · Generation backends: local-motion (ffmpeg recipes), mock, modal + openrouter placeholders, backend selection, ffmpeg in the image
  - Files: `apps/api/app/adapters/{motion_recipes,local_motion_adapter,mock_model_adapter,modal_adapter,openrouter_adapter,backend_selection}.py`, `apps/api/app/adapters/fixtures/{mock-video.mp4,mock-poster.jpg}`, `Dockerfile`, `apps/api/tests/{test_local_motion_adapter,test_backend_selection}.py`
  - Verify: `uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q tests/test_local_motion_adapter.py tests/test_backend_selection.py && docker build -t hf-clone . && docker run --rm --entrypoint ffmpeg hf-clone -version && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-003-1
- [ ] **T-003-7** · End-to-end smoke on local compose (api + worker + MinIO + local-motion) and STATUS lines for AC-1..AC-8
  - Files: `scripts/smoke-generation`
  - Verify: see brief (starts api + worker, then `scripts/smoke-generation --base-url http://localhost:8000`)
  - Suggested role: reviewer (a different model from the T-003-4 and T-003-5 implementers) · Depends on: T-003-3, T-003-4, T-003-5, T-003-6
