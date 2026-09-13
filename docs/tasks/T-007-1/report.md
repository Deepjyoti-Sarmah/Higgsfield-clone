# Report T-007-1

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `apps/api/app/routers/share.py` — replaced the T-007-0 `501` body with the real public read. The frozen surface is unchanged: handler `read_public_job`, `response_model=PublicJobResponse`, `responses={404: {"model": ErrorResponse}}`, `job_id: uuid.UUID`. Added `storage`/`settings` `Depends` (they do not appear in `openapi.json`).
- `apps/api/app/services/share_views.py` (new) — `PublicJobView` + `read_public_job(session, storage, settings, job_id) -> PublicJobView | None`: one primary-key job read, one preset lookup, one batched asset lookup (no N+1). Only the two **output** assets are fetched — the input asset is never read, so there is nothing private to leak.
- `apps/api/tests/test_share_api.py` (new) — 7 tests (cookie-free read, exact key set, 404, 422, succeeded URLs, failed-job privacy, preset fallback, same-bytes-for-everyone).
- `docs/tasks/T-007-1/report.md` (this file).
- **Not committed**, and `docs/STATUS.md` / `docs/WORKLOG.md` were **not** touched: the brief scopes this task to the four paths above and says the orchestrator handles docs sync and the commit. No other file was modified.

## Reused
- `app/repositories/jobs.py::find_job` (primary-key read), `repositories/presets.py::find_active_preset`, `repositories/assets.py::find_assets_by_ids`.
- `app/adapters/object_storage.py::build_asset_url` (presigned GET, or `S3_PUBLIC_BASE_URL`-joined).
- conftest fixtures `client` (no cookie), `guest_client`, `other_guest_client`, `object_storage`; `tests/job_api_helpers.py` (`create_queued_job`, `current_user_id`, `PRESET_NAME`).
- `get_session`, `get_object_storage`, `get_settings` — the same dependency trio `routers/jobs.py` uses.
- **The ready-only URL rule is mirrored, not imported.** `services/job_views.py` is in flight in another task's working tree, so `share_views.py` reproduces its `_asset_url`/`_ready_url` three-line rule with `build_asset_url` (as the brief instructs). A reviewer may prefer extracting it into one shared helper later.

## Verify output (full paste, no summarising)
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
-> exit 0

$ uv --directory apps/api run alembic upgrade head
-> exit 0

$ uv --directory apps/api run ruff check .
All checks passed!
-> exit 0

$ uv --directory apps/api run mypy
Success: no issues found in 30 source files
-> exit 0

$ uv --directory apps/api run pytest -q
........................................................................ [ 59%]
..................................................                       [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
122 passed, 2 warnings in 52.92s
-> exit 0

$ scripts/export-openapi
wrote packages/contracts/openapi.json
-> exit 0

$ git diff --exit-code packages/contracts/openapi.json
-> exit 0 (byte-identical)

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

=== verify command: all steps exit 0 ===
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **Privacy is asserted, not assumed.** Four tests compare the response key set to exactly the seven `PublicJobResponse` fields, so an extra field cannot leak in silently. A failed job is given a distinctive `error_message` and the test asserts that string never appears anywhere in the response body, plus that `error_message` and `prompt` are absent keys.
- **The ready-only URL rule is duplicated** (3 lines) from `services/job_views.py`. Deliberate per the brief (that file is in another task's working tree); extracting a shared `asset_url` helper is a clean follow-up.
- **A running `app.worker` was stopped before pytest**, as the brief requires — it would have claimed steps from the jobs the tests create. I also reaped a leaked `uvicorn` on `:8011` that I had left running from an earlier task. Another agent's `uvicorn --reload` dev server was deliberately left alone.
- **The suite runs against the DB in the gitignored `.env.local`** (local Postgres in this working tree — `host_is_neon: False`), so `docker compose up -d --wait db` is what the tests actually use; the worker had to be stopped because it shares that same database.
- **422 for a malformed uuid** is asserted even though the brief notes it comes from the frozen path param — cheap, and it pins the documented error.
- **No contract change:** `scripts/export-openapi` rewrote the file and `git diff --exit-code` passed, so `packages/contracts/openapi.json` is byte-identical (AC-11).
- `mypy` now reports 30 source files (was 29 before `share_views.py` was added) — clean.

## Proposed STATUS.md line (WORKS)
| Public share API `GET /api/v1/public/jobs/{job_id}`: cookie-free `200` for any existing job whatever its status, `404` for an unknown id, `422` for a malformed uuid; returns **exactly** the 7 public fields (no owner id, prompt, credit_cost, asset ids, input image or error_message); poster/video URLs only when the asset is `ready`; `preset_name` falls back to the slug | `apps/api/app/routers/share.py`, `apps/api/app/services/share_views.py`, `apps/api/tests/test_share_api.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` → 122 passed (7 new), mypy clean (30 files), contract byte-identical, 0 violations (full output in `docs/tasks/T-007-1/report.md`) | 2026-09-13 15:13 |
