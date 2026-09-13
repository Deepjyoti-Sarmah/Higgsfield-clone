# Report T-003-3

**Agent / model / tool:** implementer · deepseek-flash (DeepSeek Harness) · direct tool calls in the DSH Web GUI
**Result:** DONE

## Files changed
- `apps/api/app/services/presets.py` (new): `read_presets(session)` → active presets via `repositories/presets.list_active_presets`.
- `apps/api/app/services/uploads.py` (new): `create_pending_upload` (uuid4 asset, key `users/{user_id}/inputs/{asset_id}.{jpg|png|webp}`, `pending` insert + commit, presigned PUT), `mark_upload_complete` (404/409/422 rules, object delete on mismatch, `mark_asset_ready`), `build_input_storage_key`, `_asset_url` via `build_asset_url`. Typed errors `UploadNotFoundError` / `UploadObjectMissingError` / `UploadSizeMismatchError`.
- `apps/api/app/services/credits.py` (new): `read_balance(session, user_id)` → `sum_user_balance`.
- `apps/api/app/services/guest_accounts.py` (edit): `insert_guest_user` then `insert_ledger_entry(kind="GRANT", amount=GUEST_GRANT_CREDITS)` and ONE commit, so the user row and grant land together.
- `apps/api/app/routers/presets.py` (edit): real handler, no auth.
- `apps/api/app/routers/uploads.py` (edit): thin handlers; service errors mapped to 404 / 409 / 422.
- `apps/api/app/routers/credits.py` (edit): thin handler returning `CreditsResponse`.
- `apps/api/tests/test_presets_api.py` (new): AC-1.
- `apps/api/tests/test_uploads_api.py` (new): AC-2 (201/401/422, 409, idempotent 200 + url, size mismatch deletes the object, oversized object, other guest 404).
- `apps/api/tests/test_credits_api.py` (new): AC-7 (401, fresh guest `{"balance": 60}`, grant written once).
- `packages/contracts/openapi.json`: untouched — re-exported only to prove byte-identity (`git diff --exit-code` exit 0).

## Reused
- `require_current_user`, `get_session`, `get_settings`, `get_object_storage` (dependency-injected, override-compatible).
- `build_asset_url` from `app/adapters/object_storage.py` (no second URL helper).
- Repositories from T-003-2: `list_active_presets`, `insert_asset`, `find_user_asset`, `mark_asset_ready`, `insert_ledger_entry`, `sum_user_balance`, `insert_guest_user`.
- `domain/credit_rules.GUEST_GRANT_CREDITS`; `ErrorResponse`; fixtures `client` / `guest_client` / `other_guest_client` / `object_storage` / `session_maker`.
- `MAX_UPLOAD_BYTES` is defined once in `services/uploads.py`; a unit test asserts it equals `schemas/uploads.py::MAX_UPLOAD_BYTES` so the two cannot drift.

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
Success: no issues found in 15 source files

$ uv --directory apps/api run pytest -q
............................................                             [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
44 passed, 2 warnings in 5.79s

$ scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
wrote packages/contracts/openapi.json
openapi.json unchanged (exit 0)
```
Exit code of the whole verify chain: 0.
`44 passed` = the 29 tests that existed before T-003-3 plus the 15 added here (3 presets + 9 uploads + 3 credits).

## Standards check
```
$ scripts/check-standards
apps/web/src/features/create-video/useImageUpload.ts: 235 lines (max 200)
check-standards: FAIL (1 violations)
```
The single violation is **not** in a T-003-3 file: `apps/web/src/features/create-video/useImageUpload.ts` is an untracked in-flight file owned by the concurrent T-004-1 (create-video web) agent (it grew from 217 to 235 lines while this task ran). Per the hard rules I did not touch it.

Applying the same rules to every file this task changed yields 0 violations (max 141 lines, no comment block > 3):
```
   8  apps/api/app/services/presets.py
 101  apps/api/app/services/uploads.py
   9  apps/api/app/services/credits.py
  19  apps/api/app/services/guest_accounts.py
  18  apps/api/app/routers/presets.py
  86  apps/api/app/routers/uploads.py
  21  apps/api/app/routers/credits.py
  32  apps/api/tests/test_presets_api.py
 141  apps/api/tests/test_uploads_api.py
  24  apps/api/tests/test_credits_api.py
my files: ok (0 violations)
```
Action for the orchestrator: re-run `scripts/check-standards` after the web agent trims that file. It should then pass end to end.

## Acceptance checks
- AC-1: signed-out `GET /api/v1/presets` → 200, 12 presets, every contract field present, every `credit_cost == 20` (`test_presets_api.py`, 3 tests).
- AC-2: jpeg/png/webp → 201 with `upload_url` + `upload_headers`; `image/gif` and `byte_size = MAX+1` → 422; signed out → 401; complete before PUT → 409 `"Upload not found in storage"`; after PUT → 200 `status:"ready"` + `url`; wrong size → 422 and the object is deleted; oversized stored object → 422; `other_guest_client` → 404; second complete → 200 (idempotent).
- AC-7: fresh guest `GET /api/v1/credits` → `{"balance": 60}`; signed out → 401.
- `openapi.json` byte-identical: verified above.

## Open issues / guesses / things skipped
- **`openapi.json` byte-identity forced two naming choices.** My first pass added a `422: ErrorResponse` entry to the complete-upload `responses` map and renamed the handlers (`create_upload_handler` etc.); `scripts/export-openapi` then changed `summary`/`operationId`/the 422 schema, breaking the AC "contract didn't move". I reverted to the stub's exact public handler names (`list_presets`, `create_upload`, `complete_upload`) and the stub's exact `responses` map, and put the distinct names on the service functions instead (`read_presets`, `create_pending_upload`, `mark_upload_complete`). The 422 is still returned at runtime with `{"detail": "Uploaded file does not match the declared size"}`; only its OpenAPI description stays "Validation Error" as it was in T-003-0.
- **"Already ready → 200 again (idempotent)" is checked before the storage read.** A second complete returns the stored asset and never re-reads/re-deletes the object. This is the reading most faithful to the brief; the 409/422 rules still apply to the first completion.
- `HTTP_422_UNPROCESSABLE_ENTITY` emits a Starlette deprecation warning. I kept the constant because the stub's `status` import and the rest of the repo use it; the replacement (`HTTP_422_UNPROCESSABLE_CONTENT`) is a repo-wide change outside this brief.
- No other file needed. No guess was made about schemas, models, repositories or migrations.
- I did not commit: the orchestrator owns docs sync (`PLAN`/`STATUS`/`WORKLOG`/task checkbox) and the commit.
- Report file: `docs/tasks/T-003-3/report.md`.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Presets, uploads (presign + complete) and credits endpoints live; new guests get a one-time 60-credit GRANT | `apps/api/app/services/{presets,uploads,credits,guest_accounts}.py`, `apps/api/app/routers/{presets,uploads,credits}.py` | `uv --directory apps/api run pytest -q` (44 passed) + `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` | 2026-09-13 |
