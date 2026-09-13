# Brief T-009-8: fix the SSE ownership check so image jobs stream

You are the **implementer** for this one bug-fix task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Found by: `docs/tasks/T-009-7/report.md` (§ "One upstream bug found") — live evidence, `GET /api/v1/jobs/{image_id}/events` → 404.
- Contract: `packages/contracts/openapi.json` — the route and its `JOB_EVENT_STREAM_RESPONSE` map are **frozen**; this task changes no route and no schema.
- Code: `apps/api/app/routers/jobs.py` (`stream_job_events`), `apps/api/app/services/job_views.py` (`read_owned_job`), `apps/api/app/repositories/jobs.py` (`find_user_job`, `read_job_status`).
- Spec: `docs/specs/009-image-create/spec.md` AC-6 (live progress for image jobs), AC-11 (image jobs stay out of the video read).

## The bug (reproduce it first)
`stream_job_events` authorises with `read_owned_job(...)`, and that path cannot describe an image job:
1. `find_user_job` filters `Job.kind == "video"` (added by T-009-1 for AC-11), so an image job is `None` → 404.
2. Even without that filter, `read_owned_job` returns `None` when `preset_slug is None or input_asset_id is None` — both NULL for image jobs → 404.

So `GET /api/v1/jobs/{job_id}/events` never streams an image job, and T-009-1's/T-009-4's "the shared SSE route still streams both kinds" is false. The page only works because the watcher falls back to polling.

## Goal
The SSE route authorises on **ownership only** (kind-agnostic), so video and image jobs both stream, while `GET /api/v1/jobs/{job_id}` stays video-only and image reads stay on `GET /api/v1/image-jobs/{job_id}`.

## Allowed files (touch nothing else)
- `apps/api/app/repositories/jobs.py` — add an ownership-only lookup, e.g. `find_owned_job(session, user_id, job_id) -> Job | None` with **no** `kind` filter. Leave `find_user_job` and `list_owned_jobs` untouched (they keep the video filter).
- `apps/api/app/routers/jobs.py` — in `stream_job_events`, replace the `read_owned_job` call with that ownership check. Drop the now-unused `storage`/`settings` `Depends` parameters (they are invisible in `openapi.json`, so the contract does not move). Keep the handler name, the route, `response_class=EventStreamResponse` and the `responses=JOB_EVENT_STREAM_RESPONSE` map exactly as they are.
- `apps/api/tests/test_job_events_api.py` — add the regression tests.
- `docs/tasks/T-009-8/report.md`

## Rules
- **Do not** make `read_owned_job`/`read_job` kind-agnostic: `GET /jobs/{image_id}` must still 404 (AC-11).
- **Do not** touch `apps/api/app/services/job_views.py` beyond what is strictly required (ideally not at all) — `read_owned_job` keeps serving the video read.
- No route, schema, or migration change. `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` must stay clean.
- A non-owner must still get a plain JSON **404** on `/events` (no existence leak), and a malformed uuid still 422s.

## Acceptance checks
- [ ] `GET /api/v1/jobs/{image_job_id}/events` as its owner → **200** `text/event-stream` (it used to 404); the first frame carries the job's current status.
- [ ] `GET /api/v1/jobs/{video_job_id}/events` as its owner → still 200 `text/event-stream` (no regression).
- [ ] `GET /api/v1/jobs/{image_job_id}` (the JSON read) → still **404**.
- [ ] `GET /api/v1/jobs/{someone_elses_job}/events` → 404 for both kinds.
- [ ] no cookie → 401; malformed uuid → 422.
- [ ] `openapi.json` byte-identical; ruff + mypy clean; the full pytest suite green.

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
Stop any running `app.worker` before pytest — it races the suite on the shared dev DB.

## Out of scope
- The video path, the image read route, the worker, the web app.
- Any other bug. If you find one, report it; do not fix it here.

## Report
Write `docs/tasks/T-009-8/report.md` using `docs/templates/report.md`, and include the before/after curl evidence for the image-job `/events` route. Don't commit; the orchestrator handles docs sync and the commit.
