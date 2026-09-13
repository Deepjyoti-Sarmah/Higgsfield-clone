# Brief T-005-1: API — `GET /api/v1/jobs` (the Library list)

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/005-library/spec.md` (AC-3, AC-4, AC-12)
- Design: `docs/specs/005-library/design.md` sections **API contract**, **Data**, **Flow**, **Files**
- Contract: `packages/contracts/openapi.json`, path `GET /api/v1/jobs` → `LibraryListResponse { items: LibraryItemResponse[] }`
- Patterns: `apps/api/app/repositories/jobs.py`, `apps/api/app/services/job_views.py` (reuse `_ready_url`), `apps/api/app/routers/jobs.py` (the 501 stub you replace), `apps/api/tests/test_job_reading_api.py`, `apps/api/tests/conftest.py` (`client`, `guest_client`, `other_guest_client`, `object_storage`)

## Goal
Replace the `list_jobs` 501 stub with the real owner-scoped list: newest-first, bounded by `limit`, with a thumbnail chosen poster → input image → null, so the Library page can render without any further API call.

## Allowed files (touch nothing else)
- `apps/api/app/repositories/jobs.py` (add `list_owned_jobs` only)
- `apps/api/app/services/job_views.py` (add `LibraryItemView` + `list_owned_jobs_view`; keep `read_owned_job` as is)
- `apps/api/app/routers/jobs.py` (replace the `list_jobs` body only)
- `apps/api/tests/test_library_api.py` (new)
- `docs/tasks/T-005-1/report.md`

## Rules
- `list_owned_jobs(session, user_id, limit) -> list[Job]`: `SELECT ... WHERE job.user_id = :user_id ORDER BY job.created_at DESC, job.id DESC LIMIT :limit`. Repositories only `flush()`, never `commit()`, and hold no business rules.
- **Do not change the frozen handler surface.** The openapi operation is already published: the handler must stay named `list_jobs`, keep `response_model=LibraryListResponse`, keep `responses={401: {"model": ErrorResponse}}`, and keep the `limit` parameter exactly as `Annotated[int, Query(ge=1, le=100)] = 50`. Changing any of them moves `openapi.json` and fails this task's verify.
- Reuse `_ready_url` for every URL; do not write a second URL builder. `thumbnail_url` = poster when ready, else the input image when ready, else `None`. `video_url` = the ready output video, else `None`.
- `preset_name` falls back to the preset slug when the preset row is gone (the existing `read_owned_job` rule).
- Another user's jobs must be **absent**, not 404 (no existence leak).
- Add no migration and no model change: `ix_job_user_created` already covers the query.

## Acceptance checks
- [ ] `GET /api/v1/jobs` as `guest_client` → 200; items are only that guest's jobs, **newest first**
- [ ] `limit` defaults to 50 and bounds 1..100; `?limit=0` and `?limit=101` → 422; `?limit=1` returns exactly 1
- [ ] signed out (`client`) → 401
- [ ] `other_guest_client`'s list excludes the first guest's jobs, and vice versa
- [ ] thumbnail rule: a succeeded job exposes its ready poster as `thumbnail_url`; a job whose poster is not ready but whose input image is ready exposes the input image; a job with neither exposes `None`
- [ ] a `failed` job carries its `error_message`; a `queued` job has `video_url is None`
- [ ] `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` → **byte-identical**
- [ ] `ruff`, `mypy` (strict on `app/services`) and the full pytest suite are green

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
- Any other route, schema, model or migration. If you believe the frozen `LibraryItemResponse` is wrong, **stop and say so in the report** — do not change it here.
- Delete (P1), pagination cursors (P1), SSE/live status (P1), and all `apps/web/**` work.
- `apps/api/app/schemas/jobs.py` is frozen by T-005-0; do not edit it.

## Report
Write `docs/tasks/T-005-1/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
