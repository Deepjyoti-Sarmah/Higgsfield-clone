# Brief T-009-4: API image surface — create, read and the public options route

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/009-image-create/spec.md` (AC-4, AC-5, AC-7, AC-9, AC-11)
- Design: `docs/specs/009-image-create/design.md` §§ **API contract**, **Flow 1–4 and 8**, **Files**
- Provided by T-009-1: `repositories/image_jobs.py` (`insert_image_job`, `insert_job_image`, `list_job_images`, `find_owned_image_job`), the `job.kind`/params model, the video-only filters
- Provided by T-009-3: `adapters/backend_selection.py::select_image_adapter` (not needed here), `domain/image_rules.py` (`image_credit_cost`, the literals, `MAX_IMAGE_COUNT`, the cost constants)
- Existing: `apps/api/app/services/{job_creation.py,job_views.py,credits.py}`, `apps/api/app/routers/{jobs.py,credits.py,image_jobs.py (the T-009-0 stubs)}`, `apps/api/app/repositories/{jobs,assets,presets}.py`, `apps/api/app/schemas/{jobs.py,image_jobs.py}`

## Goal
The three image routes work: a one-transaction create with a HOLD, an owner read that returns ready `image_urls` + the backend, and the public options payload.

## Allowed files (touch nothing else)
- `apps/api/app/services/image_job_creation.py` (new)
- `apps/api/app/services/image_job_views.py` (new)
- `apps/api/app/services/image_options.py` (new)
- `apps/api/app/routers/image_jobs.py` (replace the three T-009-0 stub bodies)
- `apps/api/tests/test_image_jobs_api.py` (new), `apps/api/tests/test_image_options_api.py` (new)
- `docs/tasks/T-009-4/report.md`

## Must do
- **`services/image_options.py`**: `read_image_options() -> ImageOptionsResponse` built from `domain/image_rules` (the aspect/quality literals, `MAX_IMAGE_COUNT`, `IMAGE_CREDIT_COST_STANDARD`/`_HIGH`). Pure, no session.
- **`services/image_job_creation.py`** — mirror `job_creation.create_job` exactly, with typed errors:
  - `ImageJobCreation {id, status, credit_cost, image_count}` and `InsufficientImageCreditsError(balance, required)` (or reuse `InsufficientCreditsError` from `job_creation` — your choice, but do not edit that file).
  - `async def create_image_job(session, user_id, *, prompt, aspect_ratio, quality, count, idempotency_key) -> ImageJobCreation`, **one transaction**: `lock_user_row` → `find_job_by_idempotency_key` (an existing job returns it; never a second HOLD) → `required = image_credit_cost(quality, count)` → `sum_user_balance` (insufficient → rollback + raise) → `insert_image_job(...)` → `insert_job_step(session, job.id, "generate_image")` → `insert_ledger_entry(kind="HOLD", amount=hold_amount(cost), job_id=job.id)` → `notify_job_event` → `commit`, with the same `IntegrityError` race re-read `create_job` does.
- **`services/image_job_views.py`**: `read_owned_image_job(session, storage, settings, user_id, job_id) -> ImageJobView | None` — owner-scoped via `find_owned_image_job`; `image_urls` from `list_job_images` → ready `output_image` assets only, through the existing `_ready_url`/`build_asset_url` rule (copy the 3-line helper the way `share_views`/`job_views` do; do not edit those files); `backend` from the job's `job_step` (the latest/only step's `backend`, `None` until it runs).
- **`routers/image_jobs.py`**: replace the three `raise HTTPException(501)` bodies. Keep every handler **name**, signature, `response_model`, `status_code` and `responses` map exactly as T-009-0 froze them — `openapi.json` must stay byte-identical. The POST maps `InsufficientImageCreditsError` to the **top-level** 402 body (`JSONResponse(status_code=402, content=InsufficientCreditsResponse(...).model_dump())`) exactly like `POST /jobs`.
- **Tests**:
  - `test_image_options_api.py`: public (no cookie) 200 with the five aspect ratios, two qualities, `max_count == 4` and the two unit costs matching `domain/image_rules`.
  - `test_image_jobs_api.py`: 401 without a cookie on POST and GET; a guest with 60 credits → POST → **202** `{status: "queued", credit_cost: 10, image_count: 1}` for `standard`/1 and `60` for `high`/4, with `GET /credits` dropping by exactly that; a fresh guest has 60 so `high`/4 (60) succeeds and a second `high`/4 → **402** with top-level `balance`/`required`, no second HOLD; the same idempotency key twice → the same id and one HOLD; `GET /image-jobs/{id}` for the owner returns the queued job with `image_urls == []`, `backend is None`; a different guest and the video-only `GET /jobs/{id}` both **404**.
- ≤200 lines per file; no request/query params added beyond the frozen ones.

## Acceptance checks
- [ ] the three routes answer as the contract says (202/402/422/401/404 included) and `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` is **byte-identical**
- [ ] exactly one `HOLD` per created job, in the same transaction as the job + step; an idempotent repeat holds nothing
- [ ] 402 body carries `balance` and `required` at the **top level** (the spec-003 convention)
- [ ] `image_urls` only ever contains **ready** `output_image` assets; `backend` is the step's backend or `None`
- [ ] ruff, mypy (strict on `app/services`) and the full suite are green

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards
```
Stop any running `app.worker` first. `test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` is a known pre-existing flake; if it fails, re-run it alone and say so.

## Out of scope
- The worker branch and the image completion (T-009-5) — this task creates queued jobs only; a test may assert the queued state, not a rendered image.
- The adapters (T-009-3), the schemas/router stubs/`main.py`/`openapi.json` (T-009-0), the migration/models/repositories (T-009-1), any web file.
- Anything in `services/job_creation.py`, `services/job_views.py`, `routers/jobs.py`, `repositories/jobs.py` — T-009-1 owns those edits.

## Report
Write `docs/tasks/T-009-4/report.md` using `docs/templates/report.md`. Don't commit; the orchestrator does.
