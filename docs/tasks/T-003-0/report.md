# Report T-003-0

**Agent / model / tool:** designer · Claude Opus 5 · Claude Code (hooks capture to `.agent-logs/`)
**Result:** DONE

## Files changed
- `docs/specs/003-generation-core/spec.md`: Status set to APPROVED (handoff counts as approval, per the brief).
- `docs/specs/003-generation-core/design.md` (new): AC map, API contract table + SSE frame format, data (5 tables, columns, FKs, checks, unique and partial indexes, migrations `0002`/`0003`), flows (create transaction, claim SQL, lease renewal, finish, reaper, NOTIFY payload, SSE broker/stream), `ModelAdapter` Protocol + 4 backends + selection, 12 presets with exact ffmpeg recipes, `ObjectStorage` Protocol + key layout, settings, test plan, files table with task owners, repository signatures, reused, risks.
- `docs/specs/003-generation-core/tasks.md` (new): T-003-0 (ticked) + T-003-1 … T-003-7 with disjoint files, verify commands, dependencies, roles, waves.
- `docs/tasks/T-003-{1..7}/brief.md` (new): one filled brief per task.
- `apps/api/app/schemas/{presets,uploads,jobs,credits}.py` (new): the Pydantic contract.
- `apps/api/app/routers/{presets,uploads,jobs,credits}.py` (new): handlers with the final signatures, auth dependency and documented error responses, all raising 501.
- `apps/api/app/main.py`: includes the 4 new routers.
- `packages/contracts/openapi.json`: regenerated.
- `docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md`: state updates.

## Reused
- `require_current_user` (all signed-in stubs), `ErrorResponse` from `app/schemas/user.py`, the router style of `routers/auth.py`, `scripts/export-openapi`.
- The design builds on `app/db.py` (`Base`, `get_session`, `create_database_engine`, `create_session_maker`), the `open_client` conftest pattern and the `0001` migration style.

## Verify output (full paste, no summarising)
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
$ uv --directory apps/api run ruff check .
All checks passed!
$ uv --directory apps/api run pytest -q
.......                                                                  [100%]
7 passed in 0.26s
$ scripts/export-openapi
wrote packages/contracts/openapi.json
$ python3 -c "import json;p=json.load(open('packages/contracts/openapi.json'))['paths'];print('\n'.join(sorted(p)))"
/api/health
/api/v1/auth/guest
/api/v1/credits
/api/v1/jobs
/api/v1/jobs/{job_id}
/api/v1/jobs/{job_id}/events
/api/v1/me
/api/v1/presets
/api/v1/uploads
/api/v1/uploads/{asset_id}/complete
$ scripts/check-standards
check-standards: ok (0 violations)
```
(Blank lines and a local shell `zoxide` warning were filtered from the paste.) Extra: `uv --directory apps/api run mypy` → `Success: no issues found in 4 source files`.

**Extra checks run while designing:**
- **Disjoint files:** a script parsed every `Files:` line in `tasks.md` (expanding `{a,b}`) → `77 files; duplicates: none`.
- **ffmpeg recipes** (`/tmp/t0/recipes.py`, implementing the design's filter chain exactly) on ffmpeg 7.1.4, inputs `testsrc2` 1600×1000 jpg and 900×1400 png: all 24 renders `h264`, 1280×720 or 720×1280, `frames=120 fps=24/1 dur=5.000000`, 0.7–2.8s each; `moov` atom before `mdat` (faststart). Corner luma on every frame of `orbit-push` and `spiral-in` (both orientations) never drops below 76, so rotation shows no black corners.

## Standards check
```
check-standards: ok (0 violations)
```

## Acceptance checks
- [x] Every AC in spec 003 maps to a design section and at least one task (table at the top of design.md)
- [x] No two tasks in tasks.md share a file (script above)
- [x] Every T-003-k brief has allowed files, a verify command and out-of-scope
- [x] `openapi.json` contains all spec-003 endpoints; the 7 existing tests still pass

## Open issues / guesses / things skipped
- **Brief said "T-003-1 must be contract + migrations".** The contract (schemas + stubs + openapi) is already published here, as the brief also required, so T-003-1 is "migrations + data foundation" and only checks that the contract stays byte-identical (`git diff --exit-code packages/contracts/openapi.json`).
- **SSE in OpenAPI:** the events route uses a small `EventStreamResponse` class (`media_type = "text/event-stream"`) so `JobStatusEvent` is registered as a component. FastAPI emits `{"type": "string", "$ref": "#/components/schemas/JobStatusEvent"}` for that content type. Valid in OpenAPI 3.1, but `openapi-typescript` may type it as a string; the spec-004 client should parse frames with the `JobStatusEvent` component type explicitly.
- **Design choices not dictated by the spec (reviewer, please check):**
  - SETTLE is a 0-amount ledger row (HOLD −cost, RELEASE +cost), so `SUM(amount)` stays the balance.
  - Repeating an idempotency key with a different body returns the original job, with no 409.
  - Complete-upload with a missing object is 409; with a size mismatch it's 422.
  - The per-user `SELECT … FOR UPDATE` on `app_user` serialises credit changes.
  - Presets are seeded by migration `0003` from `app/domain/preset_catalog.py`.
  - Conftest switches from `create_all` to `alembic upgrade head`.
- **Ownership edge:** T-003-5's `worker.py` imports `select_model_adapter` from T-003-6, so T-003-6 must land before T-003-5 (recorded as a dependency).
- **Not done here:** the Modal webhook (`/hooks/modal`), the modal → openrouter fallback and the `PAID_BUDGET_CENTS` guard (invariant 5) are left for the real remote adapters, as the spec's out-of-scope implies. Noted in design § ModelAdapter.
- Not reviewed by a different model yet.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Spec 003 contract published: presets, uploads, jobs, job events (SSE), credits as 501 stubs with final schemas; design + 7 task briefs | `apps/api/app/schemas/{presets,uploads,jobs,credits}.py`, `apps/api/app/routers/…`, `packages/contracts/openapi.json`, `docs/specs/003-generation-core/` | `uv --directory apps/api run ruff check . && uv --directory apps/api run pytest -q && scripts/export-openapi && scripts/check-standards` → 7 passed, 10 paths | 2026-09-13 |
