# Brief T-004-1: Shared types, copy tables, pure helpers, `ui/` primitives and the vitest runner

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/004-create-video/spec.md` (AC-1 … AC-9; this task supplies the shared vocabulary all of them use)
- Design: `docs/specs/004-create-video/design.md` sections **Shared types**, **State machine for the canvas**, **Every UI state with exact copy**, **Accessibility** (motion + progress bars), **Preset card visuals**, **Test strategy**, **Files**
- Contract: `packages/contracts/openapi.json`, schemas `PresetResponse`, `AssetResponse`, `JobResponse`, `JobStatusEvent`, `InsufficientCreditsResponse` (types are re-exported from `apps/web/src/api/generated/schema.d.ts`, never hand-written)
- Backend context: `docs/specs/003-generation-core/design.md` § API contract (job statuses `queued|running|succeeded|failed`)
- Existing patterns to follow: `apps/web/src/ui/Button.tsx`, `apps/web/src/styles.css` (tokens), `apps/web/eslint.config.js` (enforced limits), `apps/web/package.json`

## Goal
Land the foundation every other T-004-k task imports and none of them edits: the shared types, every user-visible string, the framework-free pure helpers (phase machine, file rules, elapsed formatting, motion hints) with their vitest tests, and the four `ui/` primitives (`buttonStyles`, `ButtonLink`, `ProgressBar`, `Toast`) plus the `Button` refactor onto `buttonStyles`. Also install the test runner (`vitest@^5`, `"test": "vitest run"`). After this task the four remaining tasks can be written in parallel without touching a shared file.

## Allowed files (touch nothing else)
- `apps/web/package.json` (add `vitest@^5` as the only new devDependency and `"test": "vitest run"`)
- `apps/web/package-lock.json`
- `apps/web/src/styles.css` (`--animate-hf-motion-*` / `--animate-hf-progress` tokens + matching `@keyframes`, transforms only)
- `apps/web/src/ui/buttonStyles.ts` (new)
- `apps/web/src/ui/Button.tsx` (edit)
- `apps/web/src/ui/ButtonLink.tsx` (new)
- `apps/web/src/ui/ProgressBar.tsx` (new)
- `apps/web/src/ui/Toast.tsx` (new)
- `apps/web/src/features/create-video/createVideoTypes.ts` (new)
- `apps/web/src/features/create-video/createVideoCopy.ts` (new)
- `apps/web/src/features/create-video/canvasPhase.ts` (new)
- `apps/web/src/features/create-video/canvasPhase.test.ts` (new)
- `apps/web/src/features/create-video/imageFileRules.ts` (new)
- `apps/web/src/features/create-video/imageFileRules.test.ts` (new)
- `apps/web/src/features/create-video/elapsedTime.ts` (new)
- `apps/web/src/features/create-video/elapsedTime.test.ts` (new)
- `apps/web/src/features/create-video/presetMotionHints.ts` (new)
- `apps/web/src/features/create-video/usePrefersReducedMotion.ts` (new)
- `docs/tasks/T-004-1/report.md`

## Must reuse
- `apps/web/src/ui/Button.tsx`: extract its `baseClasses`/`variantClasses` into `buttonClasses(variant)` and import it back. Behaviour (including `isLoading`) stays identical; the only addition is the `:focus-visible` outline from the design.
- `apps/web/src/styles.css` `@theme` tokens (no new colours) and Tailwind 4.3 (`has-[…]` supported).
- `apps/web/src/api/generated/schema.d.ts` for every contract type; do not re-declare API shapes by hand.
- `apps/web/eslint.config.js` limits: `max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`. Keep the full Tailwind class names in `presetMotionHints.ts` as **literal strings** so the scanner sees them.
- design.md's copy tables are normative: the `—` is em dash (U+2014), `·` is U+00B7, `…` is U+2026, and the quotes are typographic. Copy them exactly.

## Acceptance checks
- [ ] `createVideoTypes.ts` exports exactly the types in design.md § Shared types (`Preset`, `PresetCategory`, `Asset`, `Job`, `JobStatus`, `JobStatusEvent`, `InsufficientCredits`, `PresetCategoryFilter`, `PresetsState`, `PresetSelection`, `UploadErrorKind`, `UploadState`, `ImageUploadControls`, `JobDraft`, `SubmitErrorKind`, `SubmitState`, `BalanceView`, `GenerateBlockedReason`, `CanvasPhase`, `JobWatch`, `CanvasView`, `HistoryEntry`, `GuestSessionOutcome`, `RunWithGuestSession`), all derived from `components["schemas"][…]` where the contract has them.
- [ ] `createVideoCopy.ts` holds **every** string from the design's copy tables (page/panel, Image, Preset, Prompt, Generate, canvas empty/progress/result/failure, history, announcements, toasts), matching punctuation exactly.
- [ ] `deriveCanvasPhase` implements the priority list 1 → 3 in the design; `CANVAS_TRANSITIONS` matches the transitions table; `isTerminalJobStatus` is exported and treats only `succeeded`/`failed` as terminal.
- [ ] `checkImageFile` accepts `image/jpeg`, `image/png`, `image/webp` with `0 < size ≤ 10 485 760`; rejects gif/heic, 0 bytes and 10 485 761 bytes; accepts exactly 10 485 760.
- [ ] `formatElapsed` renders `0:00`, `0:07`, `1:42`, `12:05`; a negative input → `0:00`.
- [ ] `presetMotionHints.ts` maps the design's slugs to their literal Tailwind utility strings with fallback `hf-motion-zoom-in`; `styles.css` has each `--animate-*` token and matching `@keyframes` (transforms only, scale within 1.0–1.15).
- [ ] `ProgressBar` renders `role="progressbar"` with `aria-label`, `aria-valuemin=0`, `aria-valuemax=100` and `aria-valuenow` only when determinate; `Toast` is `role="alert"` with a real action button and a `Dismiss` `aria-label` button; `ButtonLink` renders a react-router `Link` styled by `buttonClasses`.
- [ ] `vitest@^5` is the only new devDependency (peer `vite ^6.4 || ^7 || ^8` is satisfied by the installed `vite@^8.3.0`), the `test` script is `vitest run`, and tests run in the Node environment with no jsdom/testing-library.
- [ ] No file over 200 lines, no function over 40 lines, complexity ≤ 8 (`npm run lint`).

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any hook or feature component file (T-004-2/3/4/5). Import from your files, but do not create `use*.ts` hooks other than `usePrefersReducedMotion.ts`.
- `apps/web/src/App.tsx`, `apps/web/src/ui/{AppShell,EmptyState}.tsx`, `apps/web/src/api/**`, `apps/web/eslint.config.js`, `apps/web/vite.config.ts`, `apps/web/tsconfig*.json`.
- Contract/API changes. If a type you need is missing from `openapi.json`, stop and write it in the report's open issues.

## Report
Write `docs/tasks/T-004-1/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
