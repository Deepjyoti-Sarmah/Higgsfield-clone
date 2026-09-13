# Brief T-003-5: Worker (claim loop, lease renewal, completion, reaper)

You are the **orchestrator-grade implementer** for this one task (claim/lease correctness decides whether users get charged for failures). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/003-generation-core/spec.md` (AC-4, AC-5; AC-9 double-claim, failure release, lease expiry)
- Design: `docs/specs/003-generation-core/design.md` sections **Flow 2–5**, **ModelAdapter**, **Storage** (output key layout), **Repository signatures**, **Credit rules and job states**
- Decisions: D-001, D-006 in `docs/DECISIONS.md`

## Goal
`APP_ROLE=worker` claims one queued step at a time, runs the selected backend with a renewed 5-minute lease, stores the outputs, and settles or releases credits; a reaper re-queues an expired step once and then fails and refunds it.

## Allowed files (touch nothing else)
- `apps/api/app/worker.py` (replace the heartbeat loop; keep `main()` as the entrypoint)
- `apps/api/app/services/{step_claiming,generation_runs,step_completion,lease_reaper}.py`
- `apps/api/tests/fakes/scripted_model_adapter.py`
- `apps/api/tests/{test_step_claiming,test_step_completion,test_lease_reaper}.py`
- `docs/tasks/T-003-5/report.md`

## Behaviour notes
- **worker.py:** build engine + `create_session_maker`, `storage = get_object_storage()`, `adapter = select_model_adapter(settings)` (from T-003-6), `worker_id = f"{hostname}:{pid}:{uuid4().hex[:8]}"`. Loop: run the reaper when `WORKER_REAPER_SECONDS` have passed; claim; if nothing, sleep `WORKER_POLL_SECONDS`; else `run_claimed_step`. Log the backend name at startup and one line per claim/finish. Database errors are logged and retried after the poll interval, never crash the loop.
- **Services take `session_maker`, `storage`, `adapter` and settings values as parameters** (no FastAPI, no globals), so tests call them directly.
- **generation_runs:** temp dir per run (`tempfile.TemporaryDirectory`); lease renewal task every `lease_seconds / 5`; `asyncio.wait_for(adapter.generate_video(...), generation_timeout_seconds)`; lease lost → cancel the adapter call, write nothing. User-safe messages exactly as in design Flow 3.
- **step_completion / lease_reaper:** exactly Flow 4a, 4b and 5, one transaction each, using `statuses_allowed_before` from `domain/job_states.py`, `hold`/`release` amounts from `domain/credit_rules.py`, `MAX_STEP_ATTEMPTS`.
- **scripted_model_adapter:** a test double implementing `ModelAdapter` that either writes two tiny files and succeeds, raises `GenerationError("…")`, raises `RuntimeError`, or sleeps forever (for the lease-lost/timeout path).

## Must reuse
- Repositories from T-003-2, `ObjectStorage`/`InMemoryObjectStorage`, `ModelAdapter` types, `select_model_adapter` (T-003-6), `app/db.py`, the conftest fixtures. Create test jobs through the API (`guest_client`) or repositories, never raw SQL except to push `lease_expires_at` into the past.

## Acceptance checks
- [ ] Tests drain leftover queued steps first (claim until `None`), because job-creation tests leave queued steps in the shared dev DB
- [ ] **Double-claim (service level):** two `claim_step` calls in parallel with one queued step → one claim; the job is `running`; a NOTIFY was sent (listen on a raw connection, or assert through `read_job_status`)
- [ ] **Success:** job `succeeded`, 2 `ready` assets at `users/{user}/jobs/{job}/video.mp4` and `poster.jpg` exist in storage, one SETTLE 0, balance stays 40
- [ ] **Failure release:** `GenerationError("Nope")` → job `failed` with `error_message == "Nope"`, RELEASE +20, balance back to 60; `RuntimeError` → the generic message, never the exception text
- [ ] **Lost lease:** the step's `lease_owner` changed mid-run → no SETTLE/RELEASE, no job change from this worker
- [ ] **Lease expiry:** expire a running step (attempt 1) → reaper re-queues it and the job is `queued`; claim again (attempt 2), expire → reaper fails it, RELEASE +20, `error_message` is the timeout copy
- [ ] `GENERATION_BACKEND=mock` worker process runs for 6s without crashing (exit 124 from `timeout`)

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
(cd apps/api && GENERATION_BACKEND=mock timeout 6 uv run python -m app.worker; test $? -eq 124 && echo "worker ran 6s")
scripts/check-standards
```

## Out of scope
- API routes, SSE (T-003-4); ffmpeg and adapters (T-003-6); multiple steps per job, the modal→openrouter fallback, the paid budget guard, the Modal webhook.

## Report
Write `docs/tasks/T-003-5/report.md` using `docs/templates/report.md`, then follow the definition of done in `AGENTS.md` (commit per the kickoff prompt, plain message, no trailers, include `.agent-logs/`).
