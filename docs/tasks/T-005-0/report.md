# Report T-005-0

**Agent / model / tool:** orchestrator/designer · deepseek-flash · DeepSeek Harness (DSH), working directly
**Result:** DONE — spec 005 designed, tasks split, and the one new route published as schemas + a 501 stub + regenerated `openapi.json`

## Files changed
| File | New/Edit | What |
|---|---|---|
| `docs/specs/005-library/spec.md` | New | story, AC-1…AC-12, all four UI states, out of scope (delete / live progress / pagination deferred to P1) |
| `docs/specs/005-library/design.md` | New | AC→design→task map, the one API contract change, data (no migration), flow, component tree, copy table, Files table with task owners, reused, risks |
| `docs/specs/005-library/tasks.md` | New | T-005-0 (ticked) + T-005-1…T-005-5 with disjoint files, waves, verify commands |
| `docs/tasks/T-005-1/brief.md` … `T-005-5/brief.md` | New | five filled briefs from `docs/templates/delegation-brief.md` |
| `apps/api/app/schemas/jobs.py` | Edit | **+** `LibraryItemResponse`, `LibraryListResponse`; existing classes untouched |
| `apps/api/app/routers/jobs.py` | Edit | **+** the `GET /jobs` 501 stub (`limit` query, 401 responses map); existing handlers untouched |
| `packages/contracts/openapi.json` | Edit | regenerated |
| `docs/tasks/T-005-0/report.md` | New | this report |

No other file was touched. `docs/PLAN.md`, `docs/STATUS.md` and `docs/WORKLOG.md` carry the usual one-line sync.

## Why a new route (and why it is safe)
`POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}` existed, with **no list sibling**, so the Library could not be server-backed without one. The addition is `GET /api/v1/jobs` → `LibraryListResponse { items: LibraryItemResponse[] }`, owner-scoped, ordered newest-first, bounded by `?limit=` (1–100, default 50).

**No migration.** `job` already carries `Index("ix_job_user_created", "user_id", text("created_at DESC"))` (`apps/api/app/models/job.py`), which serves exactly `WHERE user_id = :id ORDER BY created_at DESC`. No model, ledger, claim/lease or worker change: the Library is read-only, so architecture invariants 1–5 are untouched.

`LibraryItemResponse` is a dedicated shape rather than a reuse of `JobResponse`, because `JobResponse` carries `prompt`/`credit_cost`/`input_asset_id`/`started_at`/`finished_at` the list never renders and would mint **three** presigned URLs per row; the item carries exactly `id`, `status`, `preset_slug`, `preset_name`, `thumbnail_url`, `video_url`, `created_at`, `error_message`.

## Verify output (full paste, no summarising)
```
$ python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))"
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
$ ls docs/tasks | grep T-005
T-005-1
T-005-2
T-005-3
T-005-4
T-005-5
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Extra verification (beyond the brief's command)
- **The contract only grew.** `git diff --stat packages/contracts/openapi.json` → `162 insertions(+)`, and a filter for deletions prints **NO DELETIONS ✓**. The new operation is `list_jobs_api_v1_jobs_get` with `limit` = `{type: integer, minimum: 1, maximum: 100, default: 50}`, `200 → LibraryListResponse`, `401`, `422`; the only new component schemas are `LibraryItemResponse` and `LibraryListResponse`. Re-running `scripts/export-openapi` afterwards leaves the file unchanged (**byte-identical**), so the frozen contract is stable.
- **The stub behaves as designed** (ASGI client, local Postgres): no cookie → `401 {"detail":"Not signed in"}`; guest session (`POST /api/v1/auth/guest` → 201) → `GET /api/v1/jobs` → **`501 {"detail":"Not implemented"}`**; `?limit=101` → **422**. So T-005-1 has a live, correct seam to fill.
- **Task-file disjointness** (script over `tasks.md`): 20 distinct files across the five build tasks, with exactly one intentional sequential hand-off — `apps/api/app/routers/jobs.py`, where T-005-0 writes the stub and T-005-1 replaces the body. T-005-0 is committed before T-005-1 starts, mirroring spec 003's T-003-0 → T-003-4 sharing of `app/main.py`. `tasks.md` states this explicitly rather than claiming a clean split it does not have.

## ⚠️ Environmental finding that blocks every API verify in this spec
`apps/api/tests/*` and the app currently run against **Neon**, not the local container: `.env.local`'s `DATABASE_URL` resolves to `ep-small-poetry-b38z9y7y-pooler.c-4.ap-southeast-1.aws.neon.tech` (T-002-4 wired it). Two consequences:

1. **`tests/test_job_events_api.py` hangs forever** (~38 tests in, reproducibly, even when that file runs alone). Neon's **pooled** endpoint is PgBouncer in transaction mode, which does not carry `LISTEN`/`NOTIFY`; the SSE broker's dedicated LISTEN connection never receives an event, so `test_stream_sends_queued_running_succeeded_within_a_second_each` waits indefinitely.
2. The rest of the suite is merely *slow* over the ~1 500 km round trip and did not finish inside 420 s.

**Proof it is environmental and not this change:** with the database overridden to the local container for one process — no file edited — `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/higgsfield uv --directory apps/api run pytest -q` gives **107 passed, 1 failed in 47.21 s**. The one failure is `tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds`, which passes **3/3** when run alone — the flaky reaper test already logged in `docs/WORKLOG.md` (2026-09-13 13:00, "1 flaky reaper test logged"). With this change in place, `ruff` and `mypy` (29 files) are clean and `openapi.json` is stable.

**Recommendation (I did not act: `.env.local` is outside this task's allowed files).** Run tests against the local Postgres, or point the API/worker at Neon's **unpooled** host (`DATABASE_URL_UNPOOLED`, already present in `.env.local`), which supports `LISTEN`/`NOTIFY`. Otherwise T-005-1's verify command — which includes `pytest -q` — will time out for reasons unrelated to its code, and the spec 003 SSE test can never pass in CI against the pooler.

## Open issues / guesses / things skipped
1. **Delete is deferred to P1**, so the Library has no destructive action and the list only grows (`limit` bounds the payload). Deleting touches stored objects and the ledger; it is not a P0 list concern.
2. **No live progress in the Library.** A queued/running item shows the status returned at fetch time; live updates stay in Create video's SSE. The spec lists this explicitly as out of scope.
3. **Single bounded page.** `?limit=` (default 50, max 100) with no cursor; if the demo needs more, that is a P1 follow-up rather than an unbounded response.
4. **The web client's typed schema is not yet regenerated.** `apps/web/src/api/generated/schema.d.ts` still lacks `LibraryItemResponse`; **T-005-2 must run `npm --prefix apps/web run gen:api`** (that file is in its allowed list). Until then, `components["schemas"]["LibraryItemResponse"]` does not type-check.
5. **`spec 005` adds a route, so the "no contract change" habit from specs 004/006 does not apply here.** Every pre-existing path/schema is untouched, but downstream verify commands must expect `openapi.json` to differ from before this commit and be stable after it.
6. **T-005-5's manual browser pass will have no browser** in this CLI environment (the same limitation recorded for T-004-5/T-006-4); its brief therefore accepts a curl-level check plus a bundle grep as the substitute.
7. **Spec approval.** `spec.md` is marked APPROVED on the same convention spec 004/006 used — handing the pack off is the user's approval. If the user wants the delete action in P0 after all, that is a spec edit plus one new route (`DELETE /api/v1/jobs/{id}`) before T-005-1 starts.
8. **Capture:** my tool cannot be wrapped by `scripts/agent-run`, so per AGENTS.md this session's transcript is exported into `.agent-logs/` at commit time.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Spec 005 (Library) designed and its one new route published: `GET /api/v1/jobs` → `LibraryListResponse { items: LibraryItemResponse[] }` as a 501 stub; 5 disjoint build tasks + briefs | `docs/specs/005-library/{spec,design,tasks}.md`, `docs/tasks/T-005-{0..5}/brief.md`, `apps/api/app/schemas/jobs.py`, `apps/api/app/routers/jobs.py`, `packages/contracts/openapi.json` | `python3 … openapi paths` → 10 paths incl. `/api/v1/jobs`; `ls docs/tasks \| grep T-005` → 5 briefs; `scripts/check-standards` → 0 violations; `openapi` diff → +162/−0; stub live → 401 / 501 / 422 | 2026-09-13 |
