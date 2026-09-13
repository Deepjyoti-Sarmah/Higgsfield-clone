# Report T-004-3

**Agent / model / tool:** implementer · deepseek-flash (DeepSeek Harness Web) · direct file edits
**Result:** DONE

## Files changed
- `apps/web/src/features/create-video/useCreateJob.ts`: `CreateJobControls` — idempotent `POST /api/v1/jobs` (fresh `crypto.randomUUID()` per `submitJob`, same draft+key on `retrySubmit`, submitting guard), prompt trim, 202/402/404/409/422/401/throw mapping, `resetSubmit`.
- `apps/web/src/features/create-video/jobStatusWatcher.ts`: framework-free `createJobStatusWatcher` + `POLL_INTERVAL_MS` / `RECONNECT_DELAYS_MS`; initial `fetchJob`, SSE `status`/`open`/`error` handling, 5 s poll fallback, bounded reconnect, terminal close, idempotent `stop()`.
- `apps/web/src/features/create-video/jobStatusWatcher.test.ts`: 9 top-level tests (fake `EventSource` + `vi.useFakeTimers()`), one per watcher rule 1–6.
- `apps/web/src/features/create-video/useJobEvents.ts`: React wrapper → `JobWatch`, per-`jobId` reset, `watcher.stop()`, `wasRequeued` on `running → queued`.
- `apps/web/src/features/create-video/useElapsedSeconds.ts`: 1 s tick while started and not ended, clamped floor seconds.
- `apps/web/src/features/create-video/useActiveJob.ts`: page-level controller; exports `ActiveJob` (and `ActiveJobControls = ActiveJob & { createJob: CreateJobControls }`).
- `docs/tasks/T-004-3/report.md`: this report.

## Reused
- `apiClient` (`apps/web/src/api/client.ts`) for `POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}`; native `EventSource` only via the injectable `openEventSource` dep.
- `createVideoTypes.ts` (T-004-1): `Job`, `JobStatus`, `JobStatusEvent`, `JobDraft`, `SubmitState`, `SubmitErrorKind`, `JobWatch`, `InsufficientCredits`, `RunWithGuestSession`, `HistoryEntry`, `ImageUploadControls`, `PresetSelection`.
- `canvasPhase.ts` (T-004-1): `isTerminalJobStatus`.
- T-004-2: `CreditsControls`/`useCredits` (`refreshCredits`, `applyKnownBalance`), `SessionHistory`/`useSessionHistory` (`recordJob`, `updateJob`, `removeJob`), `RunWithGuestSession` type contract from `useGuestSessionRunner`.
- Contract from `packages/contracts/openapi.json` (`JobCreateRequest`, `JobCreatedResponse`, `JobResponse`, `JobStatusEvent`, `InsufficientCreditsResponse`) — no hand-written request/response types for our API.

## Verify output (full paste, no summarising)
```
> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


> web@0.0.0 test
> vitest run


 RUN  v5.0.0 /home/deepjyoti/Documents/Assigment/Higgsfield/apps/web

 ✓ src/features/create-video/elapsedTime.test.ts (3 tests) 6ms
 ✓ src/features/create-video/imageFileRules.test.ts (4 tests) 12ms
 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests) 15ms
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests) 13ms
 ✓ src/features/create-video/jobStatusWatcher.test.ts (9 tests) 37ms

 Test Files  5 passed (5)
      Tests  43 passed (43)
   Start at  08:45:48
   Duration  360ms (transform 61%, import 22%, tests 12%, worker 5%)


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 34 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:  0.40 kB
dist/assets/index-CuPdW9fC.css   21.76 kB │ gzip:  4.90 kB
dist/assets/index-Dq5TjGi6.js   270.15 kB │ gzip: 86.09 kB

✓ built in 211ms
check-standards: ok (0 violations)
```

The exact command run was:
`npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
and it exited `0`.

## Standards check
```
check-standards: ok (0 violations)
```
(`npm --prefix apps/web run lint` is also clean: 0 problems. Largest new file is `jobStatusWatcher.test.ts` at 199 lines; no function exceeds 40 lines, complexity ≤ 8.)

## Open issues / guesses / things skipped
- **T-004-5 wiring contract (read this):** `useActiveJob` **folds `useCreateJob` in** (the brief explicitly allows this) and returns `ActiveJob & { createJob: CreateJobControls }`. The page calls it once and uses `activeJob.createJob.state` / `.retrySubmit` for `GenerateSection` + the submit toast, `activeJob.watch` for the canvas, and `activeJob.startJob(draft)` on Generate. Call it as
  `useActiveJob({ run, history, credits, upload, selection })` where `run` is the single `useGuestSessionRunner` result and `history`/`credits`/`upload`/`selection` are the T-004-2 hook returns. There is **no** separate `useCreateJob` call in the page and no ref-setter step.
- `ActiveJobDeps.upload` is accepted (the design lists it) but unused: "Make another" deliberately keeps the image. Removing it would change the design's deps shape, so it stays.
- Watcher guesses where the design is silent:
  - A **network** result on the **initial** `fetchJob` starts the 5 s poll (the poll is the documented fallback for a GET that cannot be read).
  - A **terminal poll** result calls `onStatus` then `stop()` without a second final `fetchJob` — the poll body is already the full `JobResponse` with URLs/`error_message`.
  - A **`missing`** result during the terminal final fetch stops silently (no `onMissing`); the terminal path already delivered the job.
- Brief wording "a non-terminal or unknown `job_id` frame is ignored" is implemented as: an **unparseable** frame or a frame whose `job_id !== jobId` is ignored, while a valid non-terminal frame **is** delivered (design rule 2). The "late non-terminal poll must not override live" rule is the separate `isPolling`-gated path (test 5).
- `useElapsedSeconds` returns raw seconds (design signature `useElapsedSeconds(...): number`); `elapsedTime.formatElapsed` is applied by T-004-5's `JobProgressView`, as the design states.
- No contract/API changes were needed; every path and schema used is already in `openapi.json`.
- Not committed (per the brief); the orchestrator owns docs sync and the commit.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| T-004-3 job hooks: idempotent create, SSE watcher + 5 s poll fallback, `useJobEvents`, `useElapsedSeconds`, `useActiveJob` | `apps/web/src/features/create-video/useCreateJob.ts`, `jobStatusWatcher.ts`, `useJobEvents.ts`, `useElapsedSeconds.ts`, `useActiveJob.ts` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` (exit 0, 43 tests) | 2026-09-13 03:16 UTC |
