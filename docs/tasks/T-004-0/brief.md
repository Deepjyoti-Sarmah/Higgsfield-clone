# Brief T-004-0: Design spec 004 (Create video page)

You are the **designer** (strong reasoning plus frontend/UX sense) for this one task. First steps:
1. Read `AGENTS.md`, `docs/STATUS.md` and `docs/STANDARDS.md`.
2. Read every link below.
3. Follow `docs/playbooks/spec-new.md` steps 4–7.

**Depends on T-003-0:** `packages/contracts/openapi.json` must already contain the spec-003 endpoints (presets, uploads, jobs, job events, credits). If it doesn't, STOP and report BLOCKED.

## Context links
- Spec: `docs/specs/004-create-video/spec.md` (AC-1 … AC-9). Handing it off counts as the user's approval, so set Status: APPROVED.
- Backend design: `docs/specs/003-generation-core/design.md` (contract, SSE event shape, error codes)
- Contract: `packages/contracts/openapi.json`
- Research: `docs/research/flows/video-create.md`, screenshot `docs/research/screenshots/16-video-create-empty.png`, and the "Better than the original" section of `docs/research/product-map.md`
- Existing web code to reuse (the patterns are set):
  - `apps/web/src/ui/{Button,AppShell,EmptyState}.tsx`
  - `apps/web/src/api/client.ts` (typed openapi-fetch client)
  - `apps/web/src/features/session/useSession.ts` (session state, `startGuestSession`)
  - `apps/web/src/styles.css` (design tokens), `apps/web/eslint.config.js` (enforced limits)
- Templates: `docs/templates/design.md`, `docs/templates/tasks.md`, `docs/templates/delegation-brief.md`

## Goal
A design precise enough that 3–5 implementer agents can build the page in parallel, each owning disjoint files, and the result looks like one coherent, polished product.

## Deliverables
1. **`docs/specs/004-create-video/design.md`** covering:
   - **Route + layout:** desktop two-column, mobile stacked, with breakpoints.
   - **Component tree:** every component with its props and the file it lives in (`features/create-video/…`), and which existing `ui/` primitives it uses. New shared primitives (e.g. `ui/DropZone`, `ui/ProgressStatus`, `ui/VideoPlayer`) only where the rule of two applies.
   - **Hooks:**
     - `usePresets`
     - `useImageUpload` (presign → PUT with progress → complete)
     - `useCreateJob` (idempotency key per click, 402 handling)
     - `useJobEvents` (EventSource → status, auto-reconnect, 5s poll fallback)
     - `useCredits`
     - `useSessionHistory` (last 6 in `sessionStorage`)
     - For each: inputs, outputs, error cases, and the exact API paths from openapi.json.
   - **State machine for the canvas:** empty → uploading → ready → submitting → queued → generating → succeeded | failed, with allowed transitions.
   - **Every UI state** from the spec, with the exact copy text.
   - **The auto-guest flow** (AC-5) as a sequence.
   - **`?preset=<slug>`** deep-link handling.
   - **Accessibility:** keyboard selection of presets, focus management after upload, `aria-live` for status.
   - **Files table** (each ≤200 lines, with a responsibility), **Reused**, **Risks**.
2. **`docs/specs/004-create-video/tasks.md`:** 3–5 tasks (`T-004-1…`) with **disjoint** files, a verify command each, and dependencies. Hooks and UI primitives come first; page assembly comes last.
3. **`docs/tasks/T-004-k/brief.md`** for every task, fully filled in from the template.

## Allowed files
- `docs/specs/004-create-video/**`, `docs/tasks/T-004-*/**`
- `docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md`

## Must reuse
- The `ui/` primitives, `api/client.ts`, `useSession`, and the design tokens in `styles.css`. No new UI framework or state library.

## Acceptance checks
- [ ] Every AC in spec 004 maps to a design section and to at least one task
- [ ] Every API call in the design names a path that exists in `openapi.json`
- [ ] No two tasks share a file; every brief has its allowed files and verify command
- [ ] Each hook's error cases and each UI state's copy text are written out explicitly

## Verify command (paste the full output in report.md)
```
python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))"
ls docs/tasks | grep T-004
scripts/check-standards
```

## Out of scope
- Writing any `apps/web` code. The T-004-k tasks do that.
- Backend changes. If the contract is missing something, list it under "Open issues" in the report.

## Report
Write `docs/tasks/T-004-0/report.md` from `docs/templates/report.md`, then commit per the kickoff prompt (plain message, no trailers, include `.agent-logs/`).
