# Report T-009-8

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## The bug, reproduced first
`GET /api/v1/jobs/{image_id}/events` returned **404**, because `stream_job_events` authorised with
`read_owned_job(...)`, which cannot describe an image job (both of its lookups filter/require video-only
columns). Before the fix, against a live API on `:8000` with a real guest, video job and image job:
```
$ curl -sN --max-time 3 -b cookies http://127.0.0.1:8000/api/v1/jobs/$VIDEO/events     # video
HTTP/1.1 200 OK
content-type: text/event-stream; charset=utf-8
retry: 3000

event: status
data: {"job_id":"b64fbe04-...","status":"queued"}

$ curl -s -b cookies http://127.0.0.1:8000/api/v1/jobs/$IMAGE/events                  # image
HTTP/1.1 404 Not Found
content-type: application/json
{"detail":"Job not found"}
```
Same ownership/status for the two kinds — the asymmetry is the bug.

## Files changed
- `apps/api/app/repositories/jobs.py` (edit, `+6`): added `find_owned_job(session, user_id, job_id)` — **ownership only, no `kind` filter**. `find_user_job` and `list_owned_jobs` are untouched and keep `Job.kind == "video"`.
- `apps/api/app/routers/jobs.py` (edit, `+2/−4`): `stream_job_events` now authorises with `find_owned_job(...)` and no longer takes the `storage`/`settings` `Depends` (both were only needed by `read_owned_job`). Handler name, route, `response_class=EventStreamResponse` and `responses=JOB_EVENT_STREAM_RESPONSE` are byte-identical. `read_owned_job` is still imported and still used by `read_job` (line 127) for the video JSON read; the `ObjectStorage`/`Settings` imports are still used by `list_jobs`/`read_job`, so ruff has no unused import.
- `apps/api/tests/test_job_events_api.py` (edit, 168 → 200 lines): two regression tests + a small `_image_job` helper.
- `docs/tasks/T-009-8/report.md`: this report.

The exact source diff:
```diff
+async def find_owned_job(session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> Job | None:
+    """Ownership only, kind-agnostic: the SSE route streams image jobs too."""
+    result = await session.execute(select(Job).where(Job.id == job_id, Job.user_id == user_id))
+    return result.scalar_one_or_none()

@@ async def stream_job_events
-    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
-    settings: Annotated[Settings, Depends(get_settings)],
 ) -> EventStreamResponse:
-    view = await read_owned_job(session, storage, settings, user.id, job_id)
-    if view is None:
+    # Ownership only: an image job has no preset/input for read_owned_job to describe.
+    if await find_owned_job(session, user.id, job_id) is None:
         raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
```

## Reused
- `repositories/jobs.py`'s existing `select(Job)` style; `require_current_user`, `get_session`, `get_job_event_broker`, `stream_job_status_events` — the SSE plumbing itself is unchanged.
- The test file's existing helpers (`open_broker`, `transition`, `create_queued_job`) and the established `app.state.job_event_broker` pattern.
- No new dependency, no route, no schema, no migration, no model change.

## Verify output (full paste, no summarising)
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
docker exit=0
alembic exit=0
All checks passed!
ruff exit=0
Success: no issues found in 40 source files
mypy exit=0
........................................................................ [ 42%]
........................................................................ [ 84%]
...........................                                              [ 100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
171 passed, 2 warnings in 49.53s
pytest exit=0
wrote packages/contracts/openapi.json
export exit=0
contract-diff exit=0
check-standards: ok (0 violations)
standards exit=0
```
`171 passed` = the 169 before this task + my 2. `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` exited **0**: the contract is byte-identical (the two dropped `Depends` were never in the schema). A worker was checked first — none running.

**The first run hit the known pre-existing flake** `tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` (171 tests → 170 passed, 1 failed, the documented shared-DB race). Isolated re-run → `1 passed in 0.80s`, then the green full run above.

## Before / after curl evidence
**After the fix** (same live API, reloaded):
```
--- image /events (was 404) ---
HTTP/1.1 200 OK
content-type: text/event-stream; charset=utf-8
retry: 3000

event: status
data: {"job_id":"01724f19-3f58-42ea-86e9-3605bf75c138","status":"queued"}

--- video /events (unchanged) ---
HTTP/1.1 200 OK
content-type: text/event-stream; charset=utf-8
retry: 3000

event: status
data: {"job_id":"b64fbe04-aed4-48bc-bbb9-c8a27675e3cb","status":"queued"}
```
Both streams stay open (`curl` exit 28 = its own `--max-time`), i.e. they really stream. Boundaries after the fix:
```
image JSON read /api/v1/jobs/{image}:         HTTP 404   (AC-11 preserved)
image read /api/v1/image-jobs/{image}:        HTTP 200
another guest /events on the image job:       HTTP 404   {"detail":"Job not found"}
another guest /events on the video job:       HTTP 404
no cookie /events:                            HTTP 401
malformed uuid /events:                       HTTP 422
```

## Standards check
```
check-standards: ok (0 violations)
```
`test_job_events_api.py` is exactly **200 lines** (the limit), `repositories/jobs.py` 108, `routers/jobs.py` 172; `find_owned_job` is 4 lines. `mypy --strict` green (40 files).

## Acceptance checks
- [x] image job `/events` as owner → **200** `text/event-stream`, first frame carries the current status (`"status":"queued"` live; the test drives it to `failed` and asserts the frame).
- [x] video job `/events` as owner → still 200 `text/event-stream` (live above + the existing `test_events_endpoint_streams_for_the_owner`).
- [x] `GET /api/v1/jobs/{image_id}` (the JSON read) → still **404** (`test_events_and_the_video_read_keep_their_404_and_422_boundaries` + live).
- [x] someone else's job → 404 for **both** kinds (same test + live).
- [x] no cookie → 401 (existing test); malformed uuid → 422 (new assertion + live).
- [x] `openapi.json` byte-identical; ruff + mypy clean; full suite green (**171 passed**).

## Open issues / guesses / things skipped
- **The 200-line bound forced a compromise.** The brief asks for four separate regression cases in this one file, but it was already 168 lines. I added an image-owner stream test plus **one merged boundaries test** (video-read 404 + malformed-uuid 422 + non-owner 404 for both kinds) so the file lands on exactly 200. The scenarios are all covered and named; a reviewer wanting them as separate tests would need a new file (outside this task's allowed list).
- **`read_owned_job` is deliberately untouched** (`job_views.py` has no diff at all — the brief's "ideally not at all" is met). `GET /jobs/{id}` keeps 404ing for image jobs; image reads stay on `/image-jobs/{id}`. Confirmed by grep: `read_owned_job` is still used by `read_job`.
- **Depends removal is contract-neutral** and proven: the two params were dependency-only (no path/query/body), and the export diff is clean.
- **Environment note:** the API was down when I started, so I ran `uv run uvicorn app.main:app --port 8000 --reload` in a background job for the live repro/after evidence, and I stop it after this report. No `app.worker` ran at any point.
- The known reaper flake fired once (pre-existing, unrelated) and passed alone — recorded above.
- **No commit** (per the brief). No docs sync (STATUS/WORKLOG/PLAN) — the orchestrator owns that.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Image-job SSE fixed: `GET /api/v1/jobs/{job_id}/events` authorises on **ownership only** (`find_owned_job`, kind-agnostic) instead of `read_owned_job`, so image and video jobs both stream `text/event-stream`; the video JSON read still 404s image ids and image reads stay on `/image-jobs/{id}`; route/schema byte-identical | `apps/api/app/repositories/jobs.py`, `apps/api/app/routers/jobs.py`, `apps/api/tests/test_job_events_api.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` → 171 passed (2 new), mypy clean (40 files), contract byte-identical, 0 violations; live curl: image `/events` **200 text/event-stream** (was 404), video unchanged, non-owner 404, no-cookie 401, bad uuid 422 | 2026-09-13 23:33 |
