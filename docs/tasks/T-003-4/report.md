# Report T-003-4

**Agent / model / tool:** implementer · deepseek-flash (DeepSeek Harness) · direct tool calls in the DSH Web GUI
**Result:** DONE

## Files changed
- `apps/api/app/services/job_creation.py` (new): Flow 1 in ONE transaction — `lock_user_row` → idempotency lookup → active preset → caller's `input_image` asset (`kind` + `ready`) → `sum_user_balance` → `insert_job` + `insert_job_step('generate_video')` + `insert_ledger_entry(HOLD, -cost)` → `notify_job_event` → `commit`; `IntegrityError` on `uq_job_user_idempotency_key` rolls back and returns the winning row. Returns frozen `JobCreation(id, status, credit_cost)` (plain values, so nothing lazy-loads after the session closes); raises `PresetNotFoundError` / `InputAssetNotFoundError` / `InputAssetNotReadyError` / `InsufficientCreditsError(balance, required)`.
- `apps/api/app/services/job_views.py` (new): `read_owned_job(session, storage, settings, user_id, job_id) -> JobView | None` via `find_user_job`; preset name via `find_active_preset` (falls back to the slug); URLs via `find_assets_by_ids` + `build_asset_url`, only for assets whose `status == "ready"`.
- `apps/api/app/services/job_event_broker.py` (new): `JobEventBroker(engine)` — ONE dedicated LISTEN connection per process (`engine.connect()` → `get_raw_connection()` → `.driver_connection`, then asyncpg `add_listener('job_events')`), `subscribe`/`unsubscribe` on `dict[UUID, set[asyncio.Queue[None]]]` (`maxsize=1`, wake-ups coalesce), `add_termination_listener` → reconnect loop (1/2/4/8/16/30s) that wakes every queue after a successful reconnect, `stop()` terminates the listener so the connection never returns to the pool. Exposes `parse_job_id` (junk payloads are ignored).
- `apps/api/app/services/job_event_stream.py` (new): `stream_job_status_events(job_id, broker, session_maker, ping_seconds=20.0)` — subscribe **before** the first read, `retry: 3000`, first `status` frame immediately, then `asyncio.timeout(ping_seconds)` on the queue (`: ping` on timeout), re-read with `read_job_status` in its own short session, one `event: status` frame per status change via `JobStatusEvent.model_dump_json()`, stop after a terminal status, `finally: unsubscribe` (also on client disconnect).
- `apps/api/app/job_event_dependencies.py` (new): `get_job_event_broker(request)` (async, so it is not offloaded to the threadpool) returning `request.app.state.job_event_broker`.
- `apps/api/app/routers/jobs.py` (edit): replaced the three 501 stubs. `POST /jobs` returns 202 `JobCreatedResponse` for both a fresh and a repeated key, and `JSONResponse(402, InsufficientCreditsResponse(...).model_dump())` for insufficient credits; typed service errors → 404 / 409. `GET /jobs/{job_id}` returns `JobResponse` from `read_owned_job`, `None` → 404. `GET /jobs/{job_id}/events` checks ownership first (404 plain JSON), then resolves the broker and returns `EventStreamResponse(..., headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})`. `EventStreamResponse`, `NOT_OWNED_RESPONSE`, `JOB_EVENT_STREAM_RESPONSE` and the endpoint names/status codes are unchanged, so `openapi.json` does not move.
- `apps/api/app/main.py` (edit): lifespan starts `JobEventBroker`, stores it on `app.state.job_event_broker`, stops it in `finally` before `engine.dispose()`. Routers, static-file mounting and SPA handling untouched.
- `apps/api/tests/job_api_helpers.py` (new): shared fixtures-helpers (`create_ready_asset`, `create_pending_asset`, `post_job`, `create_queued_job`, `balance_of`, `count_job_rows`, `current_user_id`, constants).
- `apps/api/tests/job_event_helpers.py` (new): `open_broker`, `transition`, `notify_only`, `status_of`, `collect_events`, `drive_to_completion`, `wait_for_wake_up`.
- `apps/api/tests/test_job_creation_api.py` (new): AC-3 happy path (202 + one job/step/HOLD −20 + balance 60→40, queued step, prompt stored); 402 top-level body and no extra rows; 404 unknown preset; 404 another user's asset; 409 pending asset; 422 missing `idempotency_key`.
- `apps/api/tests/test_job_creation_idempotency_api.py` (new, orchestrator-approved extra file): same key twice → same `id` + exactly one HOLD; `asyncio.gather` concurrency → same `id` + one HOLD; different key/same body → second job and two holds.
- `apps/api/tests/test_job_reading_api.py` (new): 401 without cookie; owner reads 200 with `preset_name`, prompt, input URL; pending input has no URL; ready video/poster assets produce presigned output URLs; unknown job 404; `other_guest_client` 404 on both `/jobs/{id}` and `/jobs/{id}/events` (JSON, not SSE).
- `apps/api/tests/test_job_events_api.py` (new): SSE `queued → running → succeeded` each < 1 s after the NOTIFY; `: ping` with a shortened interval; terminal job closes after `retry` + one frame; broker wakes a subscriber on a real NOTIFY; terminate listener → reconnect → wake every subscriber; unsubscribe stops wake-ups; unknown job ends after the preamble; endpoint streams for the owner with the two required headers; 401 without cookie; published status codes still in `app.openapi()`; `parse_job_id` junk handling.
- `packages/contracts/openapi.json`: untouched — re-exported only to prove byte-identity (`git diff --exit-code` exit 0, re-confirmed after the final code state).
- Not touched by me: `apps/api/app/repositories/jobs.py` — the orchestrator applied the one-line `cast("str | None", …)` fix in `read_job_status` that mypy needed (see Open issues).

## Reused
- Repositories from T-003-2: `lock_user_row`, `find_job_by_idempotency_key`, `find_active_preset`, `find_user_asset`, `find_assets_by_ids`, `sum_user_balance`, `insert_job`, `insert_job_step`, `insert_ledger_entry`, `notify_job_event`, `find_user_job`, `read_job_status`.
- Domain: `hold_amount` (`credit_rules`), `TERMINAL_STATUSES` / `statuses_allowed_before` (`job_states`).
- `adapters/object_storage.build_asset_url`, `require_current_user`, `get_session`, `get_object_storage`, `get_settings`, `schemas.user.ErrorResponse`, `schemas.jobs.*` (unchanged), `settings.download_url_ttl_seconds`, conftest fixtures (`app`, `client`, `guest_client`, `other_guest_client`, `object_storage`, `session_maker`, `InMemoryObjectStorage`).
- No new dependencies, no new frameworks; SSE stays `StreamingResponse` + asyncpg LISTEN/NOTIFY.

## Verify output (full paste, no summarising)
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 

$ uv --directory apps/api run alembic upgrade head

$ uv --directory apps/api run ruff check .
All checks passed!

$ uv --directory apps/api run mypy
Success: no issues found in 25 source files

$ uv --directory apps/api run pytest -q
........................................................................ [ 73%]
..........................                                               [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
98 passed, 2 warnings in 44.78s

$ scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
wrote packages/contracts/openapi.json

$ scripts/check-standards
check-standards: ok (0 violations)
```

Exit code of the whole chain: `0`. Extras run to make the silent steps visible:
```
$ uv --directory apps/api run alembic current
0003 (head)

$ scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
wrote packages/contracts/openapi.json
openapi.json byte-identical (git diff --exit-code exit=0)
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```
Every T-003-4 file is ≤ 200 lines: `job_creation.py` 93, `job_views.py` 62, `job_event_broker.py` 126, `job_event_stream.py` 64, `job_event_dependencies.py` 8, `routers/jobs.py` 142, `main.py` 56, `test_job_creation_api.py` 134, `test_job_creation_idempotency_api.py` 69, `test_job_reading_api.py` 186, `test_job_events_api.py` 168, `job_api_helpers.py` 85, `job_event_helpers.py` 82. Services import no FastAPI (`job_event_dependencies.py`, the only FastAPI-aware new non-router file, is outside `app/services/`).

## Open issues / guesses / things skipped
- **Two helpers files beyond the brief list.** `apps/api/tests/job_api_helpers.py` and `apps/api/tests/job_event_helpers.py` are needed to keep every test file ≤ 200 lines (STANDARDS hard gate); `test_job_creation_idempotency_api.py` was explicitly approved by the orchestrator as a scope extension. Both are pure test scaffolding, no production code.
- **`get_job_event_broker` is resolved inside the handler body, not as a `Depends` parameter.** FastAPI 0.141 solves all `Depends` parameters before the endpoint body runs, so a broker dependency made a non-owner's `/events` request raise `AttributeError: 'State' object has no attribute 'job_event_broker'` in tests (the app fixture does not run the lifespan) instead of the required plain-JSON 404. Resolving it after `read_owned_job` keeps the acceptance check "other guest gets 404 on `/events`" true and still stores the broker on `app.state` exactly as the brief asks. `apps/api/app/job_event_dependencies.py` still holds the accessor, called with the `Request`.
- **mypy needed a one-line fix outside my Allowed files.** `app/repositories/jobs.py:58` (`read_job_status` → `session.scalar(...)` returns `Any`) failed `no-any-return` as soon as any T-003-4 service imported it (baseline: 15 files green; with my imports: 25 files, 1 error). I reported it instead of editing the file; the orchestrator applied `cast("str | None", …)`. The stream uses the designed `read_job_status` (not `find_job`).
- **Reconnect is real but only indirectly asserted.** `test_broker_wakes_every_subscriber_after_a_listener_reconnect` terminates the listener and waits ≤ 5 s for the wake-up, which exercises `add_termination_listener` → `_reconnect` (first backoff 1 s) → `_wake_all`. Backoff values themselves are not unit-tested.
- **`broker._listener` is touched from one test** to kill the LISTEN connection. I deliberately did not add a test-only public accessor to production code.
- **`_release_connection` schedules `connection.close()` on the running loop** after asyncpg `terminate()`; an `asyncio` task is the only way to close the SQLAlchemy wrapper from the synchronous termination callback.
- **Idempotency race belt-and-braces.** The row lock plus the unique index are both handled: a same-key race that slips past `lock_user_row` is caught as `IntegrityError` on commit, rolled back, and answered with the winning row. The `asyncio.gather` test covers the common interleaving.
- **`ping_seconds` is a function parameter, not a query parameter**, so `openapi.json` is unchanged; the router always uses the 20 s default.
- **No paid generation was run**; tests use `GENERATION_BACKEND=mock` (conftest sets it) and this task never touches the worker or adapters.
- **Out-of-scope, not done here:** worker/claim/reaper (T-003-5), adapters (T-003-6), UI, `app/schemas/*` changes. Nothing in the schemas needed changing.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Jobs API: one-transaction create (HOLD + job + step + NOTIFY), owner-only read with presigned URLs, SSE status stream from one LISTEN connection per process | `apps/api/app/services/job_creation.py`, `job_views.py`, `job_event_broker.py`, `job_event_stream.py`, `apps/api/app/routers/jobs.py`, `apps/api/app/main.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` | 2026-09-13 03:08 UTC |
