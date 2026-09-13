# Brief T-009-6: Web UI — the Create image page and its components

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/009-image-create/spec.md` (AC-3, AC-4, AC-6, AC-7, AC-8, AC-9, AC-10)
- Design: `docs/specs/009-image-create/design.md` §§ **Component tree** (exact props), **Copy** (normative), **Accessibility**, **Files**
- Provided by T-009-2: `api/imageJobs.ts` (`useImageJob`), `api/imageOptions.ts` (`useImageOptions`, `ImageOptions`), `api/credits.ts` (`useCreditBalance`), `api/guestSession.ts`
- Existing patterns: `features/create-video/{CreateVideoPage,CreateVideoPanel,GenerateSection,JobProgressView,FailureView,createVideoCopy}.tsx`, `features/library/LibraryStates.tsx`, `ui/{Button,ButtonLink,EmptyState}.tsx`, `features/session/useSession.ts` (`SessionContextValue`)

## Goal
`/create/image` (once T-009-7 routes it) shows the composer with an honest live cost, streams progress, and renders the resulting images in a grid — every string from `imageCreateCopy`.

## Allowed files (touch nothing else)
- `apps/web/src/features/image-create/imageCreateCopy.ts` (new)
- `apps/web/src/features/image-create/imageCreateTypes.ts` (new)
- `apps/web/src/features/image-create/imageSettings.ts` (new) + `imageSettings.test.ts` (new)
- `apps/web/src/features/image-create/CreateImagePage.tsx`, `ImageComposer.tsx`, `ImageSettingsRow.tsx`, `ImageStage.tsx`, `ImageResultGrid.tsx`, `ImageFailureView.tsx` (new)
- `docs/tasks/T-009-6/report.md`

## Must do
- **`imageCreateCopy.ts`** — one exported object, byte-exact from design § Copy (plain ASCII apostrophes). Include `page`, `prompt`, `settings` (with the two label maps), `generate`, `states`, `progress`, `result`, `failure`.
- **`imageCreateTypes.ts`** — the shared types: `ImageSettings { aspectRatio; quality; count }`, `ImageSettingsControls`, `ImagePhase` (`"idle" | "submitting" | "queued" | "running" | "succeeded" | "failed" | "missing"`), `ImageBlockedReason` (`"no-prompt" | "options-unavailable"`), `ImageSubmitErrorKind`, `ImageGenerateProps`, `ImageOptionsState`.
- **`imageSettings.ts`** — pure helpers (tested, no React): `DEFAULT_IMAGE_SETTINGS`, `imageCost(options, settings)` = `settings.count * (settings.quality === "high" ? options.credit_costs.high : options.credit_costs.standard)`, `blockedReason(prompt, options)`, `deriveImagePhase(phaseInputs)`. Keep each ≤ 40 lines.
- **`CreateImagePage.tsx`** — `useOutletContext<SessionContextValue>()`, `useImageOptions()`, `useCreditBalance(session)`, `useImageJob(session)` **once each**; render `h1` + subtitle → `ImageComposer` → `ImageStage`. No child fetches.
- **`ImageComposer.tsx`** — the prompt `<textarea>` (labelled, `maxLength=500`, visible counter from `prompt.counter(value)`), `ImageSettingsRow`, and a Generate section using `ui/Button` with `generate.withCost(cost)` (or `generate.blockedNoPrompt`/`generate.submitting`), the balance line (`generate.balanceKnown/Loading/Error`), and on 402 the `generate.insufficient(balance, required)` line plus a `ui/ButtonLink` `generate.getCredits` → `/credits`.
- **`ImageSettingsRow.tsx`** — three `<fieldset>` groups with `<legend>` (`settings.aspectLabel`, `qualityLabel`, `countLabel`): real `<input type="radio">` chips for each aspect/quality **from the options payload** (labels from the copy maps) and a count control 1..`options.max_count`. Never hard-code the values.
- **`ImageStage.tsx`** — `options` loading (`aria-busy="true"` + `sr-only` `states.loading.srText`) | options error (`ui/EmptyState` + Retry) | `submitting` | `queued`/`running` (`role="status"` announcement) | `succeeded` → `ImageResultGrid` | `failed`/`missing` → `ImageFailureView`.
- **`ImageResultGrid.tsx`** — a `<ul>` of `<li>`: one `<img src={url} alt={result.imageAlt(index, prompt)}>` per URL and a Download `<a download>` per image; `result.makeAnother`; and when `backend` is `"mock"` or `"local-motion"`, the visible `result.placeholderNotice` caption (AC-10). If `image_urls` is empty while `succeeded`, render the failure copy instead of an empty grid.
- **`ImageFailureView.tsx`** — `failure.title` (or `failure.missing`), `failure.retry`, `failure.makeAnother`.
- **Zero user-visible string literals** in the `.tsx` files; one `h1`; every status is text; the phase live region is `role="status"` and the error `role="alert"`.
- `imageSettings.test.ts`: cost for standard/1, high/4 and a mid case; `blockedReason` for an empty and a whitespace prompt; `deriveImagePhase` for each input combination.

## Acceptance checks
- [ ] AC-4: the Generate label shows the computed cost **before** generating and changes with quality/count; the allowed aspect/quality values come from the API response, not from a hard-coded list
- [ ] AC-3: Generate is disabled with a text reason while the prompt is empty
- [ ] AC-5/AC-9: submitting disables the button; a 402 shows the balance/required and a `/credits` link
- [ ] AC-6: queued/running are announced in a polite live region; no second watcher/hook is added
- [ ] AC-7/AC-10: exactly `count` images with descriptive `alt` + Download, and a placeholder caption for a placeholder backend
- [ ] AC-8: a failed job shows the failure copy and never an image
- [ ] one `h1`; no colour-only state; every file ≤ 200 lines, every function ≤ 40 lines, complexity ≤ 8; `ui/` primitives reused

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- `App.tsx` and the `/create/image` route (T-009-7) — the page is reachable only after that task.
- Editing T-009-2's `api/**`, `ui/**`, `styles.css`, or any other feature; do not touch `features/create-video/**`.
- Real image models, Library/Share integration, image detail/upscale (see the spec's out of scope).

## Report
Write `docs/tasks/T-009-6/report.md` using `docs/templates/report.md`. Don't commit; the orchestrator does.
