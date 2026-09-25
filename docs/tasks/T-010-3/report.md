# Report T-010-3

**Agent:** muse-spark@opencode · **Role:** implementer · **Result:** PARTIAL

## Files changed
- `apps/api/app/repositories/sequence_jobs.py` (new, 74 lines): `insert_sequence_job`, `insert_sequence_clips` (position = index, clips[0] forced `"cut"`), `find_clip_source_jobs` (own jobs only), `find_owned_sequence_job`, `list_sequence_clips` (clip + source poster id, position order)
- `apps/api/app/services/sequence_job_creation.py` (new, 136 lines): `create_sequence_job` follows design steps 2–6 (lock → replay → limits → clip/audio validation → balance → one-transaction writes → IntegrityError race replay); `SequenceClipNotFoundError`, `SequenceClipIneligibleError(job_id, reason)`, `AudioAssetNotFoundError`; `IdempotencyKeyConflictError` imported from `image_job_creation`
- `apps/api/app/services/sequence_job_views.py` (new, 76 lines): `read_owned_sequence_job` → `SequenceJobResponse | None`; thumbnails from source posters, `has_audio`, video/poster URLs only when succeeded + ready
- `apps/api/app/routers/sequence_jobs.py` (116 lines): stub bodies replaced (signatures, paths, `responses=` kept; `body: SequenceJobCreateRequest` added for parsing); maps 404/422/402/429; local `_insufficient_credits_response`/`_limit_response` equivalents — the image router's are private and moving them is out of scope
- `apps/api/tests/test_sequence_jobs_api.py` (new, 200 lines, 9 tests): all 8 brief bullets via HTTP + DB asserts (HOLD/step/clip rows, replay-holds-once, key conflict, 404/422 matrix, 402 + no row, 429 at cap, GET own/foreign)
- `MIN_CLIPS`/`MAX_CLIPS` are used for the boundary payloads in tests; the service trusts the schema bounds exactly as `image_job_creation` trusts count 1–4

## Reused
- `lock_user_row`, `find_job_by_idempotency_key`, `enforce_creation_limits`, `InsufficientCreditsError`, `hold_amount`, `insert_ledger_entry`, `sum_user_balance`, `insert_job_step`, `notify_job_event`, `find_user_asset`, `build_asset_url`, `find_assets_by_ids`, `SEQUENCE_CREDIT_COST`, `STITCH_STEP_KIND`; image files as style models; `guest_client`/`session_maker`/helper fixtures

## Verify output (brief's command + openapi + standards)
```
db Healthy; alembic upgrade head ok
ruff check . → All checks passed!
mypy → Success: no issues found in 49 source files
pytest -q → 2 failed, 244 passed
  FAILED tests/test_contract_010.py::test_create_returns_501 - assert 404 == 501
  FAILED tests/test_contract_010.py::test_read_returns_501 - assert 404 == 501
  (T-010-1's file, outside Allowed files — not fixed. The stubs are gone by design:
  random-UUID clips now correctly 404 on validation; unknown job ids 404 on read.
  Owner of that file: expect 404, or use real clips and expect 202/200.)
export-openapi → wrote packages/contracts/openapi.json; diff vs pre-run copy: empty (unchanged)
scripts/check-standards → ok (0 violations)
```

## Standards check
```
check-standards: ok (0 violations)
```

## Acceptance checks (yes/no + evidence)
- [x] yes — one `session.commit()` in the service; balance checked before any insert; replay writes nothing (HOLD count stays 1, asserted)
- [x] yes — no cross-module private imports (local router helpers, noted above); all files ≤ 200 lines (74/136/76/116/200); verb+noun names, no banned names
- [x] yes — export produces byte-identical `openapi.json`
- [ ] partial — ruff ✓ mypy ✓ check-standards ✓; pytest 244 passed + the 2 T-010-1 stub-behavior failures above

## Open issues / guesses / things skipped
- PARTIAL only for the two `test_contract_010.py` stub assertions; everything in scope is done. No commit; no new dependencies.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Sequence API with HOLD + idempotency (T-010-3 PARTIAL: 2 T-010-1 stub tests now 404-by-design) | `repositories/sequence_jobs.py`, `services/sequence_job_{creation,views}.py`, `routers/sequence_jobs.py` | ruff+mypy clean, `test_sequence_jobs_api.py` 9 passed, openapi diff empty | 2026-09-25 |

## Orchestrator follow-up (Claude Opus 5.5, 2026-09-25)
- Removed `test_create_returns_501` and `test_read_returns_501` from `tests/test_contract_010.py`. The routes now have real behaviour, which `test_sequence_jobs_api.py` covers.
- The reviewer's fixes to `test_stitch_runs.py` (undefined `_drain_queued_steps`, 207 → 200 lines) are recorded in the T-010-6 review.
- Follow-up (non-blocking): `stitch_clips` should accept `str | Path` for `work_dir`.
