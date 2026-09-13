# Report T-005-1

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (dsh) agent
**Result:** DONE

## Files changed
- `apps/api/app/repositories/jobs.py`: added `list_owned_jobs(session, user_id, limit)` — `WHERE job.user_id = :user_id ORDER BY job.created_at DESC, job.id DESC LIMIT :limit`; read-only, no `flush()` and no business rules.
- `apps/api/app/services/job_views.py`: added `LibraryItemView` + `list_owned_jobs_view` (and the private `_referenced_asset_ids` / `_library_item_view` helpers); every URL goes through the existing `_ready_url`/`_asset_url`. `thumbnail_url` = ready poster, else ready input, else `None`; `video_url` = ready output video else `None`; `preset_name` falls back to the slug. `read_owned_job` untouched.
- `apps/api/app/routers/jobs.py`: replaced the `list_jobs` 501 stub body. Handler name, `response_model=LibraryListResponse`, `responses={401: {"model": ErrorResponse}}` and `limit: Annotated[int, Query(ge=1, le=100)] = 50` are unchanged. Added `storage`/`settings` `Depends` (same pattern as `read_job`) and the `LibraryItemResponse` import; deps do not appear in `openapi.json`.
- `apps/api/tests/test_library_api.py` (new): 7 tests — 401 signed out; empty list; newest-first order + item shape; `limit` truncates to the newest and `0`/`101` → 422; cross-guest isolation (foreign jobs absent, not 404); thumbnail poster → input → `None`; failed `error_message` + queued `video_url is None`; `preset_name` slug fallback when the preset is inactive.
- `docs/tasks/T-005-1/report.md`: this report.

## Reused
- `_ready_url` + `_asset_url` from `services/job_views.py` (no second URL builder), `find_assets_by_ids`, `list_active_presets`, `create_queued_job`/`current_user_id`/`PRESET_NAME` test helpers, the `guest_client` / `other_guest_client` / `object_storage` / `session_maker` fixtures, `ErrorResponse` and the frozen `LibraryItemResponse`/`LibraryListResponse` schemas, and the existing `ix_job_user_created` index (no migration).

## Verify output (full paste, no summarising)
```
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
All checks passed!
Success: no issues found in 29 source files
........................................................................ [ 62%]
...........................................                              [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
115 passed, 2 warnings in 53.93s
wrote packages/contracts/openapi.json
check-standards: ok (0 violations)
```

## Standards check
```
All checks passed!                                   # ruff check .
Success: no issues found in 29 source files          # mypy (strict on app/services)
check-standards: ok (0 violations)                   # scripts/check-standards
```
`scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` produced no diff: the contract is byte-identical.

## Open issues / guesses / things skipped
- The first verify run failed on the known-flaky `tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` (it claimed another test's queued step: `second.job_id != job_id`). Re-ran it alone → `1 passed in 1.48s`, then re-ran the full verify → `115 passed`. Not related to this change; the output above is the green re-run.
- The brief says "replace the `list_jobs` body only"; the new body needs the storage/settings providers, so two `Depends` parameters (identical to `read_job`) plus one import line were added. `openapi.json` is unchanged, which the diff check confirms.
- `preset_name` fallback is a slug→name map from `list_active_presets` (one query; the same `is_active` filter `find_active_preset` uses). The fallback test flips `preset.is_active` for `dolly-in` and restores it in a `finally`, so it leaves no state behind.
- `LibraryItemResponse` was left exactly as T-005-0 froze it; nothing about it looked wrong. No schema, model or migration change.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| API: `GET /api/v1/jobs` Library list (owner-scoped, newest-first, `limit` 1–100, thumbnail poster→input→null) | `apps/api/app/routers/jobs.py`, `apps/api/app/services/job_views.py`, `apps/api/app/repositories/jobs.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` | 2026-09-13 14:48 |
