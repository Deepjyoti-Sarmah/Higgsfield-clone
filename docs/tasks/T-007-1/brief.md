# Brief T-007-1: API — public read of a shared job

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/007-share/spec.md` (AC-2, AC-5, AC-8, AC-9, AC-11)
- Design: `docs/specs/007-share/design.md` sections **API contract**, **`PublicJobResponse`**, **Data**, **Flow**
- Contract: `packages/contracts/openapi.json`, path `GET /api/v1/public/jobs/{job_id}` → `PublicJobResponse`
- Patterns: `apps/api/app/services/job_views.py` (the owner-scoped view builder and its `_ready_url` rule), `apps/api/app/routers/share.py` (the 501 stub you replace), `apps/api/tests/test_job_reading_api.py`, `apps/api/tests/conftest.py` (`client`, `guest_client`, `other_guest_client`, `object_storage`)

## Goal
A stranger with a job id can read the job's public shape with **no cookie**, and the response leaks nothing private.

## Allowed files (touch nothing else)
- `apps/api/app/routers/share.py` (**the `read_public_job` body only**)
- `apps/api/app/services/share_views.py` (new)
- `apps/api/tests/test_share_api.py` (new)
- `docs/tasks/T-007-1/report.md`

## Rules
- **No auth dependency.** Do not add `require_current_user`; the route must work with no cookie and appear in `openapi.json` with no security scheme.
- **Status codes:** `200` for **any existing job whatever its status** (the page renders "still generating"/"failed" from `status`); `404 ErrorResponse` only when the job id does not exist; `422` comes from the frozen `uuid` path param.
- **The public shape is frozen** by T-007-0 (`apps/api/app/schemas/share.py`). Populate exactly: `id`, `status`, `preset_slug`, `preset_name`, `poster_url`, `video_url`, `created_at`. **Never** add the owner id, `prompt`, `credit_cost`, asset ids, the input image, or `error_message` (AC-8) — a failed job's copy is the client's, not the server's.
- `poster_url` / `video_url` are set **only when that asset is `ready`** (the `_ready_url` rule); otherwise `None`.
- `preset_name` falls back to `preset_slug` when the preset row is gone.
- **Do not edit `apps/api/app/services/job_views.py`** — it is in flight in another task's working tree. Mirror its 3-line ready-only URL rule inside `share_views.py` using `build_asset_url`, and say so in the report (a reviewer may prefer extraction later).
- **Keep the frozen handler surface:** the handler stays `read_public_job` with `response_model=PublicJobResponse`, `responses={404: {"model": ErrorResponse}}` and the `job_id: uuid.UUID` path param. Adding `storage`/`settings` `Depends` is fine (they do not appear in `openapi.json`).
- One primary-key read plus one preset lookup plus one batched asset lookup; no N+1.

## Acceptance checks
- [ ] no cookie → `200` (not 401) for a job that exists; `404` for a random uuid
- [ ] the response contains **only** the seven public keys — assert the exact key set, so a future field cannot leak in silently
- [ ] a `succeeded` job exposes `video_url` and `poster_url`; a `queued` job has both `None` and `status == "queued"`; a `failed` job has `video_url is None` and **no** `error_message` key
- [ ] `preset_name` falls back to the slug when the preset is inactive
- [ ] another guest can read the first guest's job (it is public by design), and the response never contains the owner's id or cookies
- [ ] `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` → **byte-identical**
- [ ] ruff, mypy and the full suite are green

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
- The `/v/{job_id}` HTML route and its meta tags (T-007-2).
- Any change to the schema, `job_views.py`, `main.py`, the private `GET /jobs/{job_id}` behaviour, or `apps/web/**`.
- Revocable share tokens, view counts, expiry (P1 — see the spec).

## Report
Write `docs/tasks/T-007-1/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
