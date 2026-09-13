# Brief T-004-3: Job hooks — idempotent create, SSE watcher, events, elapsed, active job

You are the **implementer** for this one task (the SSE watcher is the risky piece; an orchestrator should take it if one is available). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/004-create-video/spec.md` (AC-6 progress + SSE fallback, AC-8 failure/retry, AC-4 submit)
- Design: `docs/specs/004-create-video/design.md` sections **Hooks** (`useCreateJob`, `useJobEvents`, `useElapsedSeconds`, `useActiveJob`), **State machine for the canvas**, **Test strategy**, **Files**
- Contract: `packages/contracts/openapi.json`, paths `POST /api/v1/jobs`, `GET /api/v1/jobs/{job_id}`, `GET /api/v1/jobs/{job_id}/events`; schemas `JobCreateRequest`, `JobCreatedResponse`, `JobResponse`, `JobStatusEvent`, `InsufficientCreditsResponse`
- Backend context: `docs/specs/003-generation-core/design.md` § API contract (idempotent create, top-level 402 body, SSE frames, close-after-terminal, reaper `running → queued`)
- Types you import (do not edit): `createVideoTypes.ts`, `createVideoCopy.ts` (T-004-1); `CreditsControls` from `useCredits.ts` and `SessionHistory` from `useSessionHistory.ts` (T-004-2)
- Existing patterns: `apps/web/src/api/client.ts` (`apiClient`), `apps/web/src/features/session/useSession.ts`

## Goal
Implement the job-side hooks so the canvas can show live progress and the panel can submit exactly once per click: idempotent `POST /api/v1/jobs` with correct 402/404/409/422/network mapping, a framework-free `createJobStatusWatcher` (SSE first frame, poll fallback every 5 s, bounded reconnect backoff, terminal close) with unit tests, thin React wrappers `useJobEvents`/`useElapsedSeconds`, and the page-level `useActiveJob` controller that keeps jobs, history and credits in sync.

## Allowed files (touch nothing else)
- `apps/web/src/features/create-video/useCreateJob.ts`
- `apps/web/src/features/create-video/jobStatusWatcher.ts`
- `apps/web/src/features/create-video/jobStatusWatcher.test.ts`
- `apps/web/src/features/create-video/useJobEvents.ts`
- `apps/web/src/features/create-video/useElapsedSeconds.ts`
- `apps/web/src/features/create-video/useActiveJob.ts`
- `docs/tasks/T-004-3/report.md`

You **export** `CreateJobControls` from `useCreateJob.ts` and the `ActiveJob` type from `useActiveJob.ts`; T-004-5 imports both.

## Must reuse
- `apiClient` from `apps/web/src/api/client.ts` for `POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}`.
- `RunWithGuestSession` from T-004-1 for the create call (never call `useSession()` here).
- Native `EventSource` via the injectable `openEventSource` dep; the typed client cannot stream.
- `useCredits`, `useSessionHistory`, `useImageUpload`, `usePresetSelection` types from T-004-2 and `CreateJobControls` (this task) — `useActiveJob` orchestrates them.
- The 003 SSE facts: first frame = current status, frames only on change, server closes after terminal, `retry: 3000`, a `running → queued` re-queue frame is valid. The client must `close()` on the terminal frame before the server's close makes `EventSource` reconnect.

## Acceptance checks
- [ ] `useCreateJob` makes a fresh `crypto.randomUUID()` `idempotency_key` per `submitJob` call (36 chars, inside 8..100) and stores it with the draft; `retrySubmit()` re-sends the **same draft + same key**; a call while `submitting` is ignored (double-click guard); `resetSubmit()` → `idle`; `prompt` is trimmed and empty → `null`.
- [ ] `useCreateJob` mapping: 202 → `accepted { jobId }` + `onAccepted(data.id, draft)`; 402 → `insufficient-credits` reading top-level `balance`/`required` + `onInsufficient`; 404 → `error/input-missing`; 409 → `error/input-not-ready`; 422 → `error/invalid`; `session-failed` or a second 401 → `error/session`; throw/5xx → `error/network`.
- [ ] `jobStatusWatcher.test.ts` (fake `EventSource` + `vi.useFakeTimers()`, Node env) proves rules 1–6: terminal frame closes the ES; an `error` starts a 5 s poll; `open` stops the poll; `readyState === 2` reconnects with `RECONNECT_DELAYS_MS[min(attempt, 4)]`; a late poll cannot override a newer live frame; a non-terminal or unknown `job_id` frame is ignored; `missing` stops everything; `stop()` is idempotent and silences later callbacks; a terminal initial `fetchJob` stops without waiting for SSE.
- [ ] `useJobEvents` resets to `{ job: null, status: null, connection: "idle", isMissing: false, wasRequeued: false }` on every `jobId` change/unmount, calls `watcher.stop()`, and sets `wasRequeued` on `running → queued`, clearing it on `running`.
- [ ] `useElapsedSeconds`: `null` start → `0`; `Math.max(0, floor(((endIso ? Date.parse(endIso) : Date.now()) - start) / 1000))`; re-renders every 1000 ms only while started and not ended; formats through `elapsedTime.formatElapsed`.
- [ ] `useActiveJob` returns the exact `ActiveJob` shape in the design, exposes `handleJobAccepted`/`handleInsufficient` for the page to pass into `useCreateJob` (or folds `useCreateJob` in while keeping the same return shape), records a history entry on accept, refreshes credits after 202 and on the first terminal status, updates history on each watched `job`, removes a `missing` job, and implements `startJob`/`openHistoryEntry`/`makeAnother`/`retryFailedJob`/`dismissMissing` per design (retry works for history-reopened jobs).
- [ ] No file over 200 lines, no function over 40 lines, complexity ≤ 8 (`npm run lint`).

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- `usePresets`, `usePresetSelection`, `useCredits`, `useSessionHistory`, `useImageUpload`, `useGuestSessionRunner`, `putFileWithProgress`, `sessionHistoryStore` (T-004-2) and every component (T-004-4/5).
- `apps/web/src/App.tsx`, `apps/web/src/ui/**`, `apps/web/src/api/**`, `apps/web/package.json`, `apps/web/vite.config.ts`, `apps/web/tsconfig*.json`.
- Contract/API changes. If the SSE frame or job shape you need is missing from `openapi.json`, stop and write it in the report's open issues.

## Report
Write `docs/tasks/T-004-3/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
