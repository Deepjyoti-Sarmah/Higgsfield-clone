# Report T-009-4

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `apps/api/app/services/image_options.py` (new, 19 lines): `read_image_options()` builds the payload from `domain/image_rules` (`ASPECT_RATIOS`, `QUALITIES`, `MAX_IMAGE_COUNT`, the two unit costs). Pure, no session.
- `apps/api/app/services/image_job_creation.py` (new, 88 lines): `ImageJobCreation` + `IdempotencyKeyConflictError` + `create_image_job(...)` — the same one-transaction shape as `job_creation.create_job`: `lock_user_row` → idempotency lookup → `image_credit_cost(quality, count)` → balance check (rollback + `InsufficientCreditsError` → 402) → `insert_image_job` + `insert_job_step("generate_image")` + `HOLD` → `notify_job_event` → `commit`, with the same `IntegrityError` race re-read.
- `apps/api/app/services/image_job_views.py` (new, 46 lines): `ImageJobView` + `read_owned_image_job(...)` — owner-scoped, `image_urls` only for **ready** `output_image` assets via `build_asset_url` (the same `_ready_url` rule `job_views`/`share_views` use), `backend` from the job's step.
- `apps/api/app/repositories/image_jobs.py` (edit — **one function beyond T-009-1's list, disclosed**): `+ find_job_backend(session, job_id)` so the step's `backend` is read in the repository layer rather than the service (STANDARDS: repositories own SQL).
- `apps/api/app/routers/image_jobs.py` (edit, 62 → 113 lines): the three T-009-0 stub bodies replaced. Handler names, `response_model`s, `status_code=202` and the `responses` maps are unchanged; `read_image_job` gained the `get_object_storage`/`get_settings` `Depends` it needs to build URLs (dependency params do not appear in `openapi.json` — the diff check below proves it).
- `apps/api/tests/test_image_jobs_api.py` (new, 129 lines): 8 tests. `apps/api/tests/test_image_options_api.py` (new, 23 lines): 1 test.
- `docs/tasks/T-009-4/report.md`: this report.

## Reused
- `repositories/image_jobs.py` (T-009-1) for every image query; `repositories/jobs.find_job_by_idempotency_key` + `notify_job_event`; `repositories/job_steps.insert_job_step`; `repositories/ledger.insert_ledger_entry`/`sum_user_balance`; `repositories/users.lock_user_row`.
- `job_creation.InsufficientCreditsError` as the one insufficient-credits error (no second class with identical semantics), and the top-level 402 body shape/`InsufficientCreditsResponse` that `POST /jobs` already uses.
- `ObjectStorage` + `build_asset_url` and the ready-only `_ready_url` rule; `require_current_user`/`get_session`/`get_object_storage`/`get_settings`; `ErrorResponse`.
- Tests: `guest_client`/`other_guest_client`/`client`/`object_storage`/`session_maker`, `GUEST_GRANT`/`balance_of`/`create_queued_job`/`current_user_id`.

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
Success: no issues found in 38 source files
mypy exit=0
........................................................................ [ 43%]
........................................................................ [ 87%]
.....................                                                    [ 100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
165 passed, 2 warnings in 53.63s
pytest exit=0
wrote packages/contracts/openapi.json
export exit=0
contract-diff exit=0
check-standards: ok (0 violations)
standards exit=0
```
`165 passed` = the 142 after T-009-1 + T-009-3's 14 + my 9. The only warning is the pre-existing Starlette 422 one from `test_uploads_api.py`; my own 422 path now uses the non-deprecated `HTTP_422_UNPROCESSABLE_CONTENT`.

## Standards check
```
check-standards: ok (0 violations)
```
Sizes: `image_job_creation.py` 88 · `image_job_views.py` 46 · `image_options.py` 19 · `routers/image_jobs.py` 113 · the two test files 129 + 23 — all ≤200. `create_image_job` is ~30 lines; `mypy --strict` green over 38 files.

## Acceptance checks
- [x] the three routes answer as the contract says — `test_image_options_are_public_and_complete` (public, all values + both costs), `test_create_holds_the_credit_cost_and_reads_back` (202 → `{queued, 10, 1}`, balance 60→50, read-back with `image_urls: []`/`backend: null`), `test_four_high_quality_images_cost_the_whole_grant_then_402` (60 → 0, then 402 with top-level `balance`/`required`), `test_image_routes_need_a_cookie` (401), `test_invalid_settings_are_rejected` (422).
- [x] `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` → **byte-identical** (so adding the two `Depends` to the frozen handler did not move the contract).
- [x] exactly one `HOLD` per created job (`test_one_hold_row_is_written_per_job`) and an idempotent repeat holds nothing (`test_the_same_key_returns_the_same_job_and_holds_once`).
- [x] the 402 body carries `balance` and `required` at the **top level**, matching the spec-003 convention.
- [x] `image_urls` only ever contains **ready** `output_image` assets (empty until T-009-5's worker runs, which is the queued case asserted here); `backend` is the step's `backend` or `None`.
- [x] `GET /api/v1/jobs/{image_id}` 404s and another guest gets 404 from `GET /image-jobs/{id}` (`test_an_image_job_is_not_the_video_read_and_is_owner_scoped`).
- [x] ruff, mypy strict (38 files) and the full suite green.

## Open issues / guesses / things skipped
- **One function beyond the brief's file list** (disclosed above): `repositories/image_jobs.py` gained `find_job_backend`. The brief's Files list for T-009-4 omitted any step-backend reader, and the alternative was raw SQL inside a service, which breaks the STANDARDS layering rule. It is a 5-line addition to a file this session already owns (T-009-1).
- **A cross-kind idempotency key returns 422.** `(user_id, idempotency_key)` is shared by video and image jobs, so an image POST reusing a video job's key cannot be a truthful replay. The contract has no 409, and adding one would break AC-12's byte-identical check, so the handler maps it to **422** (already declared for the body) with a clear detail. A fresh `crypto.randomUUID()` per press makes this practically unreachable; it is nonetheless tested (`test_an_idempotency_key_cannot_cross_job_types`).
- **`_insufficient_credits_response` is duplicated** from `routers/jobs.py` (5 lines) because importing a private helper from another router is worse. Rule-of-two says extract it to a shared module; that touches `routers/jobs.py`, which is out of scope here — recorded as a P2 cleanup, like the other consolidations in the design.
- **`read_image_job` gained `storage`/`settings` `Depends`.** Intentional and contract-neutral (the same situation T-007-1 had with `read_public_job`); the byte-identical diff is the proof.
- **No image work is done yet**: this task creates queued jobs and reads them; `image_urls` stays `[]` and `backend` stays `null` until T-009-5's worker runs. The failure/refund path is T-009-5's (it reuses the existing generic `complete_step_failure`).
- No commit (per the brief). No web file, schema, migration or adapter was touched.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Image API live: `GET /images-options` (public) + `POST /api/v1/image-jobs` (one transaction: lock → idempotency → cost → HOLD → step → notify; 202/401/402/422) + owner-scoped `GET /api/v1/image-jobs/{job_id}` (ready `image_urls`, `backend`), all contract-frozen | `apps/api/app/services/{image_job_creation,image_job_views,image_options}.py`, `apps/api/app/routers/image_jobs.py`, `apps/api/app/repositories/image_jobs.py`, `apps/api/tests/test_image_{jobs,options}_api.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` → 165 passed (9 new), mypy clean (38 files), contract byte-identical, 0 violations | 2026-09-13 23:14 |
