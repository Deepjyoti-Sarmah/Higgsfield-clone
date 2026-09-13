# Brief T-004-5: Page assembly, canvas views, routes — Create video page

You are the **implementer** for this one task (the last of the wave; it wires every other T-004 file together). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/004-create-video/spec.md` (AC-1 layout, AC-6 progress, AC-7 result, AC-8 failure, AC-9 session memory; AC-5 wiring)
- Design: `docs/specs/004-create-video/design.md` sections **Route + layout**, **Component tree** + **Props**, **State machine for the canvas**, **Every UI state with exact copy** (canvas, result, failure, history, announcements, toasts), **Auto-guest flow**, **Accessibility** (focus after Generate, live status, buttons), **Files**
- Contract: `packages/contracts/openapi.json`, schema `JobResponse` (`video_url`, `poster_url`, `error_message`, `created_at`, `finished_at`, `credit_cost`)
- Types/hooks/components you import (do not edit): T-004-1 (`createVideoTypes`, `createVideoCopy`, `canvasPhase`, `elapsedTime`, `usePrefersReducedMotion`, `ui/{Button,ButtonLink,ProgressBar,Toast}`), T-004-2 (`useGuestSessionRunner`, `usePresets`, `usePresetSelection`, `useCredits`, `useSessionHistory`, `useImageUpload`), T-004-3 (`useCreateJob`, `useJobEvents`, `useElapsedSeconds`, `useActiveJob`), T-004-4 (`CreateVideoPanel`)
- Existing patterns: `apps/web/src/App.tsx` (`Placeholder` routes), `apps/web/src/ui/AppShell.tsx` (outlet context), `apps/web/src/ui/EmptyState.tsx` (`/v/:jobId` placeholder), `apps/web/src/features/home/HomePage.tsx` (`useOutletContext<SessionContextValue>()`)

## Goal
Assemble the real page: `CreateVideoPage` wires the hooks to `CreateVideoPanel`, the canvas, the history strip, the toast and the announcer (staying under the 40-line function limit by delegating to the canvas views); the canvas switches on the derived `CanvasPhase` with one stable, focusable `CanvasHeading`; result/failure/history/announcement behavior matches the copy tables; and `App.tsx` routes `/create/video` to the page and `/v/:jobId` to the `EmptyState` share placeholder.

## Allowed files (touch nothing else)
- `apps/web/src/features/create-video/CreateVideoPage.tsx`
- `apps/web/src/features/create-video/StatusAnnouncer.tsx`
- `apps/web/src/features/create-video/CreateVideoCanvas.tsx`
- `apps/web/src/features/create-video/CanvasHeading.tsx`
- `apps/web/src/features/create-video/HowItWorks.tsx`
- `apps/web/src/features/create-video/HowItWorksStep.tsx`
- `apps/web/src/features/create-video/JobProgressView.tsx`
- `apps/web/src/features/create-video/StatusSteps.tsx`
- `apps/web/src/features/create-video/ResultView.tsx`
- `apps/web/src/features/create-video/ResultActions.tsx`
- `apps/web/src/features/create-video/useResultActions.ts`
- `apps/web/src/features/create-video/FailureView.tsx`
- `apps/web/src/features/create-video/SessionHistoryStrip.tsx`
- `apps/web/src/App.tsx` (edit: replace the `/create/video` `Placeholder`, add `/v/:jobId`)
- `docs/tasks/T-004-5/report.md`

## Must reuse
- `useOutletContext<SessionContextValue>()` for the session (the page calls `useGuestSessionRunner` **once** and passes the runner into `useImageUpload` and `useCreateJob`); do not call `useSession()` inside this feature.
- `ui/Button`, `ui/ButtonLink`, `ui/ProgressBar`, `ui/Toast`, `ui/EmptyState`; `deriveCanvasPhase`/`CANVAS_TRANSITIONS`; `elapsedTime.formatElapsed`; `usePrefersReducedMotion` for video autoplay and smooth scroll.
- `useActiveJob` as the page controller (jobs, history, credits sync, retry, open history, make another); `useResultActions(job)` for Download/Share.
- Tailwind tokens in `styles.css`; no new colours.

## Acceptance checks
- [ ] `/create/video` renders inside `AppShell` with the responsive grid (one column under `md`, `md:grid-cols-[360px_minmax(0,1fr)]`, `xl:grid-cols-[420px_minmax(0,1fr)]`), the sticky panel, and the mobile order panel → canvas → history; `document.title` is `Create video · Higgsfield` while mounted and resets on unmount; `?preset=` is honoured through `usePresetSelection`.
- [ ] The page derives `CanvasPhase` from the hooks (never stores it) and `CanvasView`/`blockedReason`/`insufficient` exactly as the design's priority rules say; after `submitting` it focuses the canvas heading and on mobile scrolls the canvas into view (`behavior: "smooth"`, `"auto"` under reduced motion).
- [ ] `CreateVideoCanvas` renders `CanvasHeading` **once** above the body so focus survives view switches; `HowItWorks`/`HowItWorksStep`, `JobProgressView` + `StatusSteps`, `ResultView` + `ResultActions`, and `FailureView` (variants `failed`/`missing`) match the copy tables and step states exactly.
- [ ] `useResultActions`: Download fetches the video → blob → `higgsfield-{preset_slug}-{first 8 of id}.mp4` object-URL click → revoke, falling back to `window.open(video_url, "_blank", "noopener")`; Share copies `location.origin + "/v/" + job.id`, shows `Link copied` for 2000 ms, falls back to opening the URL; a real `<a href="/v/{id}">Open share page</a>` exists under the actions.
- [ ] `CreateVideoPage` calls `useGuestSessionRunner` once and shares it; passes `useActiveJob.handleJobAccepted`/`handleInsufficient` into `useCreateJob` (or the folded equivalent) so AC-5 and the 402 flow work with no dialog.
- [ ] `StatusAnnouncer` is `sr-only aria-live="polite" aria-atomic="true"` and emits **one** message per phase change (the page keeps the previous phase in a ref), with the exact announcement strings; `StatusSteps` marks the current pill `aria-current="step"`; toasts are `role="alert"` with submit priority over presets and no auto-dismiss.
- [ ] `SessionHistoryStrip` renders nothing for 0 entries, otherwise `This session` + tiles with the exact `aria-label`, status dot, letter fallback on image error and `aria-current="true"` on the active one; `App.tsx` routes `/v/:jobId` to the `EmptyState` ("Share page" / "Public share pages are coming soon.").
- [ ] **Manual flow check:** if `curl -s localhost:8000/api/v1/presets` returns 200 with JSON, run the AC-1/2/3/4/5/6/7/9 flow in a browser against the local stack and note the result; if it returns 501/errors, record it as **SKIPPED** in the report (the backend tasks T-003-3/4/5 gate this).
- [ ] No file over 200 lines, no function over 40 lines, complexity ≤ 8 (`npm run lint`).

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any T-004-1/2/3/4 file (import only), `apps/web/src/ui/**` edits, `apps/web/src/api/**`, `apps/web/package.json`, `apps/web/styles.css`.
- Backend changes, the real FastAPI share page (spec 007), library (005), preview videos (006).
- Contract/API changes. If a field the result view needs is missing from `openapi.json`, stop and write it in the report's open issues.

## Report
Write `docs/tasks/T-004-5/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
