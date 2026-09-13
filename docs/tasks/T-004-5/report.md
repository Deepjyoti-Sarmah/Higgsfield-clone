# Report T-004-5

**Agent / model / tool:** implementer · deepseek-flash (DeepSeek Harness Web GUI) · DSH agent tools (not wrapped by `scripts/agent-run`; this run is a delegated subagent of `session-0fff282e-…`, so its transcript lives in the harness, not `.agent-logs/`)
**Result:** DONE

## Files changed
- `apps/web/src/features/create-video/CreateVideoPage.tsx` (new, 200 lines): page controller (`useCreateVideoRunner` folded here as `useCreateVideoController`), derived phase/canvas/blockedReason/insufficient, `document.title`, focus+scroll after Generate, announcement message, one-toast-at-a-time, panel+canvas columns.
- `apps/web/src/features/create-video/StatusAnnouncer.tsx` (new): `sr-only` `aria-live="polite"` `aria-atomic="true"` region.
- `apps/web/src/features/create-video/CreateVideoCanvas.tsx` (new): single stable `CanvasHeading` + phase switch (how-it-works / progress / result / failure).
- `apps/web/src/features/create-video/CanvasHeading.tsx` (new): focusable `<h2 tabIndex={-1}>`.
- `apps/web/src/features/create-video/HowItWorks.tsx` (new): 3-step onboarding + step states per phase.
- `apps/web/src/features/create-video/HowItWorksStep.tsx` (new): one step card + CSS/inline illustrations.
- `apps/web/src/features/create-video/JobProgressView.tsx` (new): thumbnail, preset, sub copy, timer, status pills, indeterminate bar, polling line.
- `apps/web/src/features/create-video/StatusSteps.tsx` (new): Queued → Generating → Done pills with `aria-current="step"`.
- `apps/web/src/features/create-video/ResultView.tsx` (new): meta line + autoplaying (reduced-motion aware) video.
- `apps/web/src/features/create-video/ResultActions.tsx` (new): Download / Make another / Share + `Open share page` anchor.
- `apps/web/src/features/create-video/useResultActions.ts` (new): blob download with open-in-tab fallback, clipboard share with `Link copied` for 2s.
- `apps/web/src/features/create-video/FailureView.tsx` (new): `failed` (refund + error_message + Retry/Make another) and `missing` (Back to create) variants.
- `apps/web/src/features/create-video/SessionHistoryStrip.tsx` (new): not rendered at 0 entries; `This session` + tiles (aria-label, status dot, letter fallback, `aria-current`).
- `apps/web/src/App.tsx` (edit, 53 lines): `/create/video` → `CreateVideoPage`; new `/v/:jobId` → `EmptyState` ("Share page" / "Public share pages are coming soon."); `create/image`, `library`, `credits` placeholders unchanged.

No file exceeds 200 lines (largest: `CreateVideoPage.tsx` = 200 exactly).

## Reused
- T-004-1: `createVideoCopy` (every user-visible string), `createVideoTypes`, `deriveCanvasPhase`, `elapsedTime.formatElapsed`, `usePrefersReducedMotion`, `ui/Button`, `ui/ButtonLink` (indirectly via the panel), `ui/ProgressBar`, `ui/Toast`, `ui/buttonStyles.buttonClasses`.
- T-004-2: `useGuestSessionRunner`, `usePresets`, `usePresetSelection`, `useCredits`, `useImageUpload`, `useSessionHistory`.
- T-004-3: `useActiveJob` (folds `useCreateJob`; `.createJob`, `.watch`, `.startJob`, `.retryFailedJob`, `.makeAnother`, `.openHistoryEntry`, `.dismissMissing`), `useElapsedSeconds`.
- T-004-4: `CreateVideoPanel` (+ `GenerateSectionProps` type).
- Existing: `ui/AppShell` outlet context (`useOutletContext<SessionContextValue>()`), `ui/EmptyState`, `ui/Button`, react-router `Link`/`useSearchParams` (inside the hooks).

## Verify output (full paste, no summarising)
Command: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
```
> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 78 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-DBSO5s7j.css   23.70 kB │ gzip:   5.28 kB
dist/assets/index-CyLhjTDq.js   321.06 kB │ gzip: 100.40 kB

✓ built in 161ms
check-standards: ok (0 violations)
```
Exit code: 0. (`npm --prefix apps/web test` also passes: 5 files, 43 tests, unrelated to this task but run for confidence.)

## Manual flow check (browser)
`curl -s localhost:8000/api/v1/presets` → **HTTP 200, JSON, 12 presets** (and `GENERATION_BACKEND=local-motion`), so per the brief this step is **not** SKIPPED. However **no browser is available in this CLI session** (checked: no `chromium`/`google-chrome`, no `playwright`/`puppeteer`/`cypress` in `apps/web/node_modules/.bin`), so the in-browser AC-1/2/3/4/5/6/7/9 pass was **NOT RUN** and is the one acceptance check left for the orchestrator's `verify-slice`.
Substitute evidence gathered against the live local stack (`GENERATION_BACKEND=local-motion`, mock-free local backend, no paid generation):
- `POST /api/v1/auth/guest` → 201 (auto-guest, AC-5 path); `GET /api/v1/credits` → 200 `{"balance":60}`.
- `POST /api/v1/uploads` → 201 (MinIO presigned PUT, `upload_headers: {"Content-Type":"image/png"}`); `PUT` the presigned URL → 200; `POST /api/v1/uploads/{asset_id}/complete` → 200 `AssetResponse` (a wrong declared `byte_size` produced 422 "Uploaded file does not match the declared size" → the `invalid-file` rejection path).
- `POST /api/v1/jobs` before completion → 409 (maps to `input-not-ready`); after completion → **202** `{"status":"queued","credit_cost":20}`.
- `GET /api/v1/jobs/{id}` → **succeeded** with `video_url`, `poster_url`, `finished_at` (AC-6 → AC-7 data contract holds).
- `GET /api/v1/jobs/{id}/events` → `retry: 3000` then `event: status` with the terminal frame.
- `GET /api/v1/credits` after → `{"balance":40}` (20 charged); `GET video_url` → 200 `video/mp4` with `Access-Control-Allow-Origin: http://localhost:8000` (so `useResultActions` blob download can fetch it).
- SPA serves `/create/video` and `/v/abc` → 200 HTML; the production bundle contains the page copy (`Make a video in three steps`, `Your video is ready`, `Open share page`, `Generation failed`, `This session`, `Live updates paused`).
Side effect: this created one guest, one asset and one job in the running dev database/MinIO (no repo files).

## Standards check
```
check-standards: ok (0 violations)
```
ESLint (part of the verify command) reports no errors for the new/edited files: `max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`, naming-convention all satisfied.

## Open issues / guesses / things skipped
- **UI browser pass skipped** (see above). AC-1 layout, AC-2 drop/browse/paste, AC-3 chips/keyboard radio group, AC-4 button states, AC-9 strip clicks are only covered by types + build + the API-level flow, not by a real browser.
- **Guess — single heading.** `design.md` § Props gives `headingRef` to `JobProgressView`/`ResultView`/`FailureView`, but § Accessibility ("`CreateVideoCanvas` renders `CanvasHeading` once, above the view body") and the brief's acceptance ("renders `CanvasHeading` **once** above the body so focus survives view switches") contradict that. I followed the latter: `CreateVideoCanvas` owns the one heading; the views take no `headingRef`.
- **Guess — `connection` prop.** `CanvasView` (T-004-1) has no `connection` field and cannot be edited, so `CreateVideoCanvas`/`JobProgressView` take an extra `connection: JobWatch["connection"]` prop to render `Live updates paused. Checking every 5 seconds.`
- **Guess — focus after "Make another".** The preset `<fieldset ref={groupRef}>` is private to `CreateVideoPanel` (T-004-4, no ref prop), so the page focuses the first `input[name="preset"]` radio via `document.querySelector` (one line, commented) instead of extending the panel.
- **Guess — network submit errors** are deliberately **not** passed to `GenerateSection.submitError` (the copy table routes `error/network` to the toast); `GenerateSection` also maps `network` to the same toast string, which would double-render if passed.
- **Not touched / out of scope:** no T-004-1/2/3/4 file, `ui/**`, `api/**`, `styles.css`, contracts, backend. No commit made.
- **Capture note:** AGENTS.md says non-Claude-Code CLIs must run through `scripts/agent-run`; this session is a harness-delegated subagent and cannot wrap its own runtime. The orchestrator should export/copy this run's transcript into `.agent-logs/` if it is required.
- No contract field was missing: `JobResponse` provides everything the result/failure views need.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Create video page assembled: panel + canvas + history strip, routes, result/failure/announcer/toast | `apps/web/src/features/create-video/CreateVideoPage.tsx`, `apps/web/src/App.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` (browser flow pending `verify-slice`) | 2026-09-13T03:30Z |
