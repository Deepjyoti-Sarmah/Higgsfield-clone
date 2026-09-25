# Report T-010-1

**Agent:** muse-spark@opencode · **Role:** implementer · **Result:** PARTIAL

## Files changed
- `apps/api/app/schemas/sequence_jobs.py` (new): exact copy of design.md § "New and changed schemas", incl. the `transition_in` comment
- `apps/api/app/schemas/credits.py`: added `LedgerKind`, `LedgerEntryResponse`, `LedgerListResponse` per design
- `apps/api/app/schemas/jobs.py`: `JobKind` gains `"sequence"`; added `LibraryImageResponse`; `LibraryItemResponse` gains `images`/`clip_count`/`duration_ms`; nothing else touched
- `apps/api/app/schemas/uploads.py`: `UploadContentType` gains `audio/mpeg`, `audio/mp4`, `audio/wav`; `MAX_UPLOAD_BYTES` unchanged
- `apps/api/app/schemas/share.py`: `PublicJobResponse` rewritten per design (`kind` defaults `"video"`, nullable preset fields, `image_urls`/`clip_count`/`duration_ms`)
- `apps/api/app/routers/sequence_jobs.py` (new, tag `sequence-jobs`): POST 202 + GET stubs, `require_current_user`, raise 501 `Not implemented yet (T-010-3)`, `responses` 401/402/404/422/429 and 401/404
- `apps/api/app/routers/credits.py`: `GET /credits/ledger` (`Query(10, ge=1, le=50)`, 401 in `responses`), raises 501 `Not implemented yet (T-010-4)`
- `apps/api/app/main.py`: `sequence_jobs` import (ruff-isort order) + `include_router` next to image-jobs
- `packages/contracts/openapi.json`: regenerated via `scripts/export-openapi`, never hand-edited
- `apps/web/src/api/generated/schema.d.ts`: regenerated via `npm run gen:api`
- `apps/api/tests/test_contract_010.py` (new, 9 tests): paths in `app.openapi()`, 1/7-clip + bad-transition 422s, authed POST/GET 501s, `limit=0` 422, `audio/mpeg` accepted, share `kind` defaults `video`

## Reused
- `InsufficientCreditsResponse`, `LimitExceededResponse` (`schemas/jobs.py`), `ErrorResponse` (`schemas/user.py`), `JobStatus` in the new routes' `responses=`; `routers/image_jobs.py` as the router style model (prefix, `Annotated` deps, `require_current_user`); `guest_client`/`client`/`app` fixtures from `tests/conftest.py`

## Verify output (full signal; untruncated rerun: the brief's verify command)
```
docker compose up -d --wait db  →  db Healthy
alembic upgrade head  →  ok
ruff check .  →  All checks passed!
mypy  →  Success: no issues found in 46 source files
pytest -q  →  6 failed, 223 passed
contract assert  →  not reached (chain stopped at pytest); ran separately: contract ok
gen:api  →  ran separately: ok (schema.d.ts regenerated)
typecheck  →  ran separately: 2 errors (below)
scripts/check-standards  →  ok (0 violations)
```
Failures (all in files outside Allowed files; not fixed per hard rules):
```
tests/test_share_api.py::test_public_read_needs_no_cookie (also test_succeeded_job_exposes_ready_output_urls, test_failed_job_hides_the_error_message, test_every_visitor_gets_the_same_public_bytes)
  tests/test_share_api.py:80: AssertionError: assert {'clip_count'..., 'kind', ...} == {'created_at'...'status', ...}
  Extra items in the left set: 'kind', 'duration_ms', 'image_urls', 'clip_count'
  Cause: PUBLIC_KEYS (test_share_api.py:10) pins the exact share response keys; the brief mandates the 4 new fields. Owner of that file: add the keys.
tests/test_s3_object_storage.py::test_presigned_put_then_read_download_delete (+ test_presigned_put_rejects_a_different_content_type)
  httpx.ConnectError: All connection attempts failed (PUT to presigned minio URL; only the db service runs here; STATUS BROKEN notes minio/mc is unpullable). Environmental, pre-existing; app code never runs.
apps/web typecheck:
  src/features/library/LibraryItem.tsx(66,60): error TS2322: Type '"image" | "video" | "sequence"' is not assignable to type 'GenerationBadgeKind | undefined'.
  src/features/library/LibraryResultView.tsx(72,56): error TS2322: (same)
  Cause: mandated JobKind widening; both web files are out of scope (a web task must add "sequence" to GenerationBadgeKind).
```

## Standards check
```
check-standards: ok (0 violations)
```

## Acceptance checks (yes/no + evidence)
- [x] yes — schemas copied field-for-field from design.md (incl. `transition_in` comment, `Field(min_length=2, max_length=6)`, `Query(ge=1, le=50)`); 9/9 new contract tests green
- [x] yes — openapi diff vs HEAD: missing paths `[]`, changed methods `[]`, added exactly the 3 new paths
- [ ] no — suite is 223 passed + 6 failed: 4× `test_share_api.py` PUBLIC_KEYS (mandated new fields; file not in Allowed files), 2× s3 ConnectError (minio down; environmental)
- [ ] partial — `schema.d.ts` regenerated yes; web typecheck has the 2 `GenerationBadgeKind` errors above (web files out of scope)
- [x] yes for ruff/mypy/check-standards (all pass); pytest no (see above)

## Open issues / guesses / things skipped
- Result is PARTIAL only because the verify chain is red on out-of-scope files; every in-scope item is done. Recommended follow-ups: T-010-4 updates `PUBLIC_KEYS` in `test_share_api.py`; a web task widens `GenerationBadgeKind`.
- `git status` confirms only Allowed-files paths touched (plus this report).
- No commit made; no packages installed.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Spec 010 contract published, 501 stubs (T-010-1 PARTIAL: 4 share-key + 2 minio-env + 2 web-kind failures out of scope) | `apps/api/app/schemas/sequence_jobs.py`, `routers/sequence_jobs.py`, `packages/contracts/openapi.json` | `uv run ruff check` + `mypy` pass, `pytest tests/test_contract_010.py` 9 passed, openapi diff additive-only | 2026-09-25 |

## Orchestrator follow-up (Claude Opus 5.5, 2026-09-25)
- Blocker 1 fixed: `apps/api/tests/test_share_api.py` `PUBLIC_KEYS` now includes `kind`, `image_urls`, `clip_count`, `duration_ms`. The additive share contract is intended (design.md). `test_share_api.py` + `test_contract_010.py`: 16 passed.
- Blocker 2 fixed: `apps/web/src/ui/GenerationBadge.tsx` `GenerationBadgeKind` gains `"sequence"`, and `ffmpeg` is labelled "Stitched". `npm run typecheck` is clean.
- Blocker 3 (MinIO not running → 2 `test_s3_object_storage.py` errors) is environmental. Run `docker compose up -d minio` before the full suite.
