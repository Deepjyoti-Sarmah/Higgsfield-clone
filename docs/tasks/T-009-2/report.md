# Report T-009-2

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `apps/web/src/api/jobStatus.ts` (new) — `JobStatus` (from the generated schema), `TERMINAL_JOB_STATUSES`, `isTerminalJobStatus`.
- `apps/web/src/api/jobStatusWatcher.ts` (moved from `features/create-video/`) — now generic: `FetchJobResult<J>`, `WatcherDeps<J>`, `WatcherCallbacks<J>`, `createJobStatusWatcher<J extends { status: JobStatus }>`. Everything else is unchanged: the SSE URL `/api/v1/jobs/${jobId}/events`, `POLL_INTERVAL_MS = 5000`, `RECONNECT_DELAYS_MS`, the 3 final-fetch tries, `stop()`. It reads the predicate from `api/jobStatus.ts`.
- `apps/web/src/api/jobStatusWatcher.test.ts` (moved) — same 9 tests, now typed against a minimal `TestJob = { id; status }` (the watcher only ever reads `status`), which also keeps the file at 189 lines.
- `apps/web/src/features/create-video/jobStatusWatcher.ts` and `.test.ts` — **deleted**.
- `apps/web/src/features/create-video/useJobEvents.ts` — imports the moved module, `WatcherDeps<Job>` / `createJobStatusWatcher<Job>`; behaviour unchanged.
- `apps/web/src/features/create-video/canvasPhase.ts` — the predicate is gone; `JobStatus` now comes from `api/jobStatus`.
- `apps/web/src/features/create-video/useActiveJob.ts` — imports `isTerminalJobStatus` from `api/jobStatus`.
- **`apps/web/src/features/create-video/canvasPhase.test.ts` (NOT in the brief's Allowed list — see Open issues)** — its import of `isTerminalJobStatus` had to move with the predicate.
- `apps/web/src/api/credits.ts` — `+ CreditBalanceState` and `useCreditBalance(session)`; `useBalanceState` now exposes `applyBalance(next)` so both hooks share it. `useCreditsPage` is otherwise untouched. 176 lines, so no split was needed.
- `apps/web/src/api/imageOptions.ts` (new) — `ImageOptions`, `useImageOptions()` over the **public** `GET /api/v1/image-options` (no session, no guest runner).
- `apps/web/src/api/imageJobs.ts` (new) — `useImageJob(session)`: create + watch + read.
- `apps/web/src/api/generated/schema.d.ts` — regenerated.
- `docs/tasks/T-009-2/report.md` (this file).
- **Not committed**; the orchestrator does that.

## `gen:api` first (as instructed)
`ImageOptionsResponse`, `ImageJobCreateRequest`, `ImageJobCreatedResponse`, `ImageJobResponse` were absent from the client. The regeneration is **+272 insertions, 0 deletions** — purely additive: the three paths (`/api/v1/image-options`, `/api/v1/image-jobs`, `/api/v1/image-jobs/{job_id}`), the four schemas plus `ImageCreditCosts`, and the three operations. No pre-existing shape changed. Every type is derived from the schema; nothing is hand-written.

## Behaviour notes
- **`useCreditBalance`** reuses the same `useBalanceState` as the credits page: `useGuestSessionRunner` (auto-guest + exactly one 401 retry), `isMountedRef`/`requestIdRef` race guards, and `hasBalanceRef` so a refresh after a known balance never flashes `loading`.
- **`useImageJob`** mints a fresh `crypto.randomUUID()` per press (`isSubmittingRef` blocks re-entry while pending), maps `202 → accepted {jobId, creditCost}`, `402 → insufficient {balance, required}` from the top-level error body, `401`/session-failed → `"session"`, `422` → `"invalid"`, anything else/throw → `"network"`. The watch uses the moved watcher with deps `fetchJob → GET /api/v1/image-jobs/{job_id}` (`401`/`404` → `missing`) and `openEventSource`, and `retryRead()` restarts it. Phase is derived (`missing` → idle/submitting → job status), so the "ready" phase names in the brief's union map to the job's own statuses.
- Imports in every new `api/` module are `react`, `./client`, `./generated/schema`, `./guestSession`, `./jobStatusWatcher` — **no `features/**`** (grep count 0 in all five api modules).

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint

> web@0.0.0 lint
> eslint .

-> exit 0

$ npm --prefix apps/web run typecheck

> web@0.0.0 typecheck
> tsc -b

-> exit 0

$ npm --prefix apps/web run test

> web@0.0.0 test
> vitest run


 RUN  v5.0.0 /home/deepjyoti/Documents/Assigment/Higgsfield/apps/web

 ✓ src/features/create-video/imageFileRules.test.ts (4 tests) 14ms
 ✓ src/features/explore/recreateHref.test.ts (4 tests) 10ms
 ✓ src/features/explore/groupPresetsByCategory.test.ts (6 tests) 13ms
 ✓ src/features/create-video/elapsedTime.test.ts (3 tests) 8ms
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests) 35ms
 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests) 37ms
 ✓ src/features/library/formatCreatedAt.test.ts (4 tests) 13ms
 ✓ src/api/jobStatusWatcher.test.ts (9 tests) 50ms

 Test Files  8 passed (8)
      Tests  57 passed (57)
   Start at  23:09:11
   Duration  530ms (transform 57%, import 24%, tests 13%, worker 6%)

-> exit 0

$ npm --prefix apps/web run build

> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 109 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-00oqWkWO.css   27.05 kB │ gzip:   5.70 kB
dist/assets/index-BnVuolpp.js   341.73 kB │ gzip: 105.28 kB

✓ built in 360ms
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

=== T-009-2 verify: all steps exit 0 ===
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Acceptance self-checks
- `features/create-video/jobStatusWatcher.ts` and its test are gone; `grep -rln "export function createJobStatusWatcher"` prints exactly one file (`api/jobStatusWatcher.ts`).
- No feature imports the old path; the only `./jobStatusWatcher` imports are inside `api/` (`imageJobs.ts`, its own test).
- `canvasPhase.ts` no longer contains `isTerminalJobStatus`; `canvasPhase.ts`, `canvasPhase.test.ts` and `useActiveJob.ts` import it from `api/jobStatus`.
- The moved watcher's 9 tests pass unchanged in behaviour (`src/api/jobStatusWatcher.test.ts`), and `useJobEvents`/`useActiveJob`/`canvasPhase` compile with import-only changes (57 tests pass overall, same count as before the move).
- `api/credits.ts` = 176 lines, `imageJobs.ts` = 199, `jobStatusWatcher.ts` = 197, `jobStatusWatcher.test.ts` = 189 — all ≤ 200.

## Open issues / guesses / things skipped
- **I had to touch one file the brief did not list: `features/create-video/canvasPhase.test.ts`.** The brief removes `isTerminalJobStatus` from `canvasPhase.ts`, but that test imports it from there, so leaving it would have failed `npm run test`. The fix is a one-line import change (predicate now from `../../api/jobStatus`). Flagged rather than silently absorbed.
- **`imageJobs.ts` landed at 199/200 lines.** The first draft was 219 with a 42-line `useImageSubmit`; I compacted it (one-line phase union, `{ ...settings, idempotency_key }` instead of re-listing the body, a 4-line `readInsufficient`, a shorter outcome branch) rather than splitting, because the brief's Allowed list names only `api/imageJobs.ts`. There is now **no headroom** in that file: the next change to it must extract a helper module.
- **`credits.ts` did not need the `api/creditBalance.ts` split** the brief allowed for (176 lines after the addition).
- **The relative `usage` of `JobStatus`:** `createVideoTypes.ts` still exports its own `JobStatus` alias (used by many create-video files); `canvasPhase`/`useActiveJob` now use the `api/jobStatus` one. They are the same union, but there are two aliases until a later consolidation.
- **No new unit test** was added for `useCreditBalance`/`useImageJob`: both are DOM/network hooks with no pure helper, and vitest runs in the Node environment here (no jsdom) — the same limitation spec 004/008 recorded. The moved watcher test is the one that travels with this task.
- The API side of spec 009 (T-009-1/3/4/5) is not in this tree yet, so `useImageJob` compiles against the frozen contract but cannot complete a real create until those land.

## Proposed STATUS.md line (WORKS)
| Shared web plumbing for Create image: one generic SSE+poll watcher moved to `api/jobStatusWatcher.ts` (with the terminal predicate in `api/jobStatus.ts`), spec-004 behaviour unchanged and its 9 tests moved; `api/credits.ts` gains `useCreditBalance`; new `api/imageOptions.ts` (public options) and `api/imageJobs.ts` (create + watch + read, fresh idempotency key per press, 202/402/session/network mapping); typed client regenerated (+272/−0) | `apps/web/src/api/{jobStatus,jobStatusWatcher,jobStatusWatcher.test,credits,imageOptions,imageJobs}.ts`, `apps/web/src/features/create-video/{useJobEvents,canvasPhase,canvasPhase.test,useActiveJob}.ts` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` → lint/tsc clean, 57 tests (the moved watcher suite among them), 109 modules, 0 violations (full output in `docs/tasks/T-009-2/report.md`) | 2026-09-13 17:39 |
