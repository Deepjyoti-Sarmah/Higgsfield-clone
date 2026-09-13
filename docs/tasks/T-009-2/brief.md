# Brief T-009-2: Web shared data — move the watcher to `api/`, add the shared balance + image hooks

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/009-image-create/spec.md` (AC-2, AC-5, AC-6, AC-7)
- Design: `docs/specs/009-image-create/design.md` §§ **Shared web plumbing** (normative), **Flow 1–3, 5, 8**, **Files**
- Contract: `packages/contracts/openapi.json` — the three new image routes were published by T-009-0
- Existing: `apps/web/src/features/create-video/{jobStatusWatcher.ts (197 lines, already dependency-injected),jobStatusWatcher.test.ts,useJobEvents.ts,canvasPhase.ts,useActiveJob.ts,useCredits.ts,useCreateJob.ts}`, `apps/web/src/api/{client.ts,library.ts,credits.ts,guestSession.ts}`
- Precedent: T-005-2 moved the guest runner to `api/guestSession.ts`; T-006-1 moved `usePresets` to `api/presets.ts`

## Goal
One SSE+poll watcher in `api/`, generic over the job type, plus the credits and image data hooks the Create image page needs — with spec 004's behaviour unchanged.

## Allowed files (touch nothing else)
- `apps/web/src/api/jobStatus.ts` (new)
- `apps/web/src/api/jobStatusWatcher.ts` (moved from `features/create-video/jobStatusWatcher.ts`) and `apps/web/src/api/jobStatusWatcher.test.ts` (moved test)
- `apps/web/src/features/create-video/jobStatusWatcher.ts` and `.test.ts` (**delete**)
- `apps/web/src/features/create-video/useJobEvents.ts`, `canvasPhase.ts`, `useActiveJob.ts` (import-path only)
- `apps/web/src/api/credits.ts`
- `apps/web/src/api/imageOptions.ts`, `apps/web/src/api/imageJobs.ts` (new)
- `apps/web/src/api/generated/schema.d.ts` (regenerate)
- `docs/tasks/T-009-2/report.md`

## Do this first
```
npm --prefix apps/web run gen:api
```
`ImageOptionsResponse`, `ImageJobCreateRequest`, `ImageJobCreatedResponse` and `ImageJobResponse` are in `openapi.json` (T-009-0) but not yet in `schema.d.ts`. Say so in the report and what the diff added; derive every type from the generated schema, never hand-write a shape.

## Must do
- **`api/jobStatus.ts`**: `export type JobStatus = components["schemas"]["JobStatusEvent"]["status"]`, `TERMINAL_JOB_STATUSES`, and `isTerminalJobStatus(status)`. This is the predicate `features/create-video/canvasPhase.ts` owns today (line 3); move it here because the watcher is at 197 lines.
- **`api/jobStatusWatcher.ts`**: the moved watcher, made **generic over the job type** — `FetchJobResult<J> = { kind: "ok"; job: J } | { kind: "missing" } | { kind: "network" }`, `WatcherDeps<J>`, `WatcherCallbacks<J>`, `createJobStatusWatcher<J extends { status: JobStatus }>(jobId, deps, callbacks)`. Keep every behaviour byte-for-byte: the SSE URL `/api/v1/jobs/${jobId}/events`, `POLL_INTERVAL_MS = 5000`, `RECONNECT_DELAYS_MS`, the 3 final-fetch tries, `wasRequeued`-free status handling, `stop()`. Move the test with it and keep it green (it uses `deps.timers`, so it stays a Node-only test).
- **`useJobEvents.ts`**: import `createJobStatusWatcher` and the types from `../../api/jobStatusWatcher` and pass the video `Job` type as the generic argument. **`canvasPhase.ts`** and **`useActiveJob.ts`**: import `isTerminalJobStatus` (and the `JobStatus` type if needed) from `../../api/jobStatus` instead of defining/importing it locally; `canvasPhase.ts` no longer exports it. No other behaviour change.
- **`api/credits.ts`**: add `useCreditBalance(session: GuestSessionSource)` returning `{ status: "loading" | "known" | "error"; balance: number | null; refresh: () => void; applyKnownBalance: (balance: number) => void }`, using `useGuestSessionRunner` (one 401 retry after the guest session) and the `api/library.ts` race guards (`isMountedRef`/`requestIdRef`, no loading flash once known). Leave `useCreditsPage` untouched.
- **`api/imageOptions.ts`**: `export type ImageOptions = components["schemas"]["ImageOptionsResponse"]` and `useImageOptions()` → `{ status: "loading" | "ready" | "error"; options: ImageOptions | null; reload: () => void }` over the **public** `GET /api/v1/image-options` (no session, no guest runner), with the same race guards.
- **`api/imageJobs.ts`**: `useImageJob(session)` owning create + watch + read:
  - `create(settings: { prompt; aspect_ratio; quality; count })` mints a fresh `crypto.randomUUID()` idempotency key per press, POSTs through the guest runner, and maps outcomes like `useCreateJob`: `202` → `{ status: "queued", id, credit_cost }`; `402` → `insufficient { balance, required }`; `401`/session-failed → a session error; other/throw → a network error.
  - watch the job with the moved watcher (deps: `fetchJob` → `GET /api/v1/image-jobs/{job_id}` returning `ImageJobResponse`, `openEventSource` as today), polling fallback, and a `reload()` for Retry.
  - expose `{ phase: "idle" | "submitting" | "queued" | "running" | "succeeded" | "failed" | "missing"; job: ImageJobResponse | null; creditCost: number | null; insufficient: { balance; required } | null; submitError: "network" | "session" | "invalid" | null; submit(settings): void; resetSubmit(): void; retryRead(): void }`.
  - Imports only `react`, `../../api/*` modules and the generated schema — **no `features/**`**.
- Keep every file ≤ 200 lines and every function ≤ 40 lines; if `api/credits.ts` (152 lines today) would exceed 200 with `useCreditBalance`, split the new hook into `api/creditBalance.ts` and say so in the report.

## Acceptance checks
- [ ] `features/create-video/jobStatusWatcher.ts` and its test are gone; nothing still imports them; grep shows one `createJobStatusWatcher` implementation
- [ ] the moved watcher's tests still pass unchanged in behaviour, and `useJobEvents`/`useActiveJob`/`canvasPhase` compile with only import changes
- [ ] `useCreditBalance` never flashes `loading` after a known balance and retries a 401 exactly once via the runner
- [ ] `useImageJob` mints a fresh key per press, maps 402 to `insufficient`, and 202 to `queued`
- [ ] `npm run lint`, `typecheck`, `test` and `build` pass; `scripts/check-standards` is clean

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Every `.tsx` component (T-009-6) and `App.tsx` (T-009-7).
- Consolidating `features/create-video/useCredits.ts`/`useCreateJob.ts` onto the shared hooks (P2 — do **not** touch them).
- The API, the contract, `ui/**`. If a field is missing, report it instead of inventing one.

## Report
Write `docs/tasks/T-009-2/report.md` using `docs/templates/report.md`. Don't commit; the orchestrator does.
