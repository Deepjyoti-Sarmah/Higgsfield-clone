# Brief T-003-4: Jobs API (create, read, SSE events)

You are the **orchestrator-grade implementer** for this one task (one-transaction create and the SSE fan-out are core). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/003-generation-core/spec.md` (AC-3, AC-6; AC-9 idempotency, insufficient credits, SSE sequence, owner-only)
- Design: `docs/specs/003-generation-core/design.md` sections **API contract** (jobs rows + SSE frames), **Flow 1** (create transaction), **Flow 6** (NOTIFY + broker + stream), **Repository signatures**, **Risks** (ASGITransport buffering)
- Contract: `packages/contracts/openapi.json`, paths `POST /api/v1/jobs`, `GET /api/v1/jobs/{job_id}`, `GET /api/v1/jobs/{job_id}/events`
- Architecture invariants 1, 3, 4: `docs/architecture/architecture.md`

## Goal
Replace the three 501 job stubs: create a job in ONE transaction (lock → idempotency → validate → balance → job + step + HOLD → NOTIFY → commit), read it with presigned URLs, and stream status over SSE from ONE LISTEN connection per process.

## Allowed files (touch nothing else)
- `apps/api/app/services/{job_creation,job_views,job_event_broker,job_event_stream}.py`
- `apps/api/app/job_event_dependencies.py`
- `apps/api/app/routers/jobs.py`
- `apps/api/app/main.py` (lifespan: start/stop `JobEventBroker`, store on `app.state.job_event_broker`)
- `apps/api/tests/{test_job_creation_api,test_job_reading_api,test_job_events_api}.py`
- `docs/tasks/T-003-4/report.md`

## Behaviour notes
- **Create:** exactly design Flow 1. The router uses `@router.post(..., response_model=JobCreatedResponse)` and returns `JSONResponse(status_code=402, content=InsufficientCreditsResponse(detail="Not enough credits", balance=…, required=…).model_dump())` for the 402, so the body is top-level. Typed service errors → 404 / 409. Repeat key → 202 with the existing job.
- **Read:** `job_views.read_owned_job(session, storage, settings, user_id, job_id) -> JobView | None`; URLs via `build_asset_url` from `app/adapters/object_storage.py`. `None` → 404.
- **Events:** check ownership with a request session first (404 JSON), then return `EventStreamResponse(stream_job_status_events(job_id, broker, request.app.state.session_maker), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})`. Keep the existing `EventStreamResponse` class and the `responses=` dicts in `routers/jobs.py` unchanged so `openapi.json` doesn't move.
- **Broker:** subscribe before the first read; `asyncio.Queue(maxsize=1)` wake-ups; ping every 20s (make the interval a parameter of `stream_job_status_events` with default 20 so tests can shorten it); reconnect with backoff and wake every queue after a reconnect.
- Services never import FastAPI. mypy strict covers `app/services`.

## Must reuse
- Repositories from T-003-2 (`lock_user_row`, `find_job_by_idempotency_key`, `find_active_preset`, `find_user_asset`, `sum_user_balance`, `insert_job`, `insert_job_step`, `insert_ledger_entry`, `notify_job_event`, `find_user_job`, `read_job_status`, `find_assets_by_ids`), `domain/credit_rules.py`, `domain/job_states.py`, `require_current_user`, `get_session`, `get_object_storage`, the conftest fixtures.

## Acceptance checks
- [ ] AC-3: 202 `{id, status:"queued", credit_cost:20}`; the DB has one job, one queued step and one HOLD −20; the balance drops 60 → 40
- [ ] **Idempotency:** the same `idempotency_key` twice (also concurrently via `asyncio.gather`) → the same `id`, exactly one HOLD
- [ ] **Insufficient credits:** after 3 jobs (balance 0) the 4th → 402 `{"detail": …, "balance": 0, "required": 20}` and no new job/step/ledger rows
- [ ] Unknown preset → 404; another user's asset → 404; pending asset → 409; missing `idempotency_key` → 422
- [ ] **Owner-only:** `other_guest_client` gets 404 on `GET /jobs/{id}` and on `/events`
- [ ] **SSE sequence:** with a broker started on a test engine, a stream receives `queued`, then `running` and `succeeded` after the test transitions the job with `transition_job_status` + `notify_job_event` (+ commit), each within 1s; the stream ends after `succeeded`; a `: ping` appears when the interval is shortened
- [ ] `openapi.json` is byte-identical after `scripts/export-openapi`

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
scripts/check-standards
```

## Out of scope
- The worker, claim, reaper (T-003-5); adapters (T-003-6); uploads/presets/credits endpoints (T-003-3); `app/schemas/*` changes (report instead); any UI.

## Report
Write `docs/tasks/T-003-4/report.md` using `docs/templates/report.md`, then follow the definition of done in `AGENTS.md` (commit per the kickoff prompt, plain message, no trailers, include `.agent-logs/`).
