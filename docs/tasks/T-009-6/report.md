# Report T-009-6

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
All new, all under `apps/web/src/features/image-create/`:
- `imageCreateCopy.ts` — every user-visible string, one exported object plus the template helpers (ASCII only; the cost label uses a `\u00b7` escape so the file stays ASCII).
- `imageCreateTypes.ts` — `ImageSettings`, `ImageSettingsControls`, `ImagePhase`, `ImageStagePhase`, `ImageBlockedReason`, `ImageSubmitErrorKind`, `ImageBalance`, `ImageGenerateProps`, `ImageJobWatch`; re-exports `ImageOptions`/`ImageOptionsState` from `api/` instead of re-declaring them.
- `imageSettings.ts` + `imageSettings.test.ts` — the pure helpers (`DEFAULT_IMAGE_SETTINGS`, `imageCost`, `blockedReason`, `deriveImagePhase`) and 3 tests.
- `CreateImagePage.tsx`, `ImageComposer.tsx`, `ImageSettingsRow.tsx`, `ImageStage.tsx`, `ImageResultGrid.tsx`, `ImageFailureView.tsx`.
- `docs/tasks/T-009-6/report.md` (this file).
- **Not committed**; no other file touched (`App.tsx` is T-009-7's; nothing in `api/**`, `ui/**`, `styles.css` or `features/create-video/**`).

## What was built
- **`CreateImagePage`** — `useOutletContext<SessionContextValue>()` + `useImageOptions()` + `useCreditBalance(session)` + `useImageJob(session)`, each called **once**; `h1` + subtitle → `ImageComposer` → `ImageStage`. Children never fetch. Local state: the prompt, and the settings via a small `useSettingsControls()`.
- **`ImageComposer`** (internal `PromptField` + `GenerateSection`) — labelled `<textarea id="image-prompt">` with `MAX_PROMPT_LENGTH = 500`, the placeholder from copy and a visible `prompt.counter(value)`; `ImageSettingsRow` once the options are in; a `ui/Button` whose label is `generate.withCost(cost)` (or `generate.submitting`), disabled while blocked or submitting, the balance line (`balanceKnown`/`balanceLoading`/`balanceError`), the blocked text, the 402 line + `ui/ButtonLink` "Get credits" → `/credits`, and the submit error in a `role="alert"`.
- **`ImageSettingsRow`** (internal `AspectGroup`/`QualityGroup`/`CountGroup` + a generic `Chip`) — three `<fieldset>`/`<legend>` groups built **from the options payload** (`aspect_ratios`, `qualities`, 1..`max_count`), labels from `settings.aspectLabels`/`qualityLabels`/`countValue`. Every chip is a real `<input type="radio">` (visually hidden, `peer-focus-visible` ring on the visible label), so keyboard + focus work.
- **`ImageStage`** (internal `OptionsLoading`, `OptionsError`, `JobProgress`, `SucceededStage`) — options loading (`aria-busy="true"` + `sr-only` `states.loading.srText`) | options error (`ui/EmptyState` + Retry) | submitting/queued/running (`role="status"`) | succeeded (`role="status"` "ready" + `ImageResultGrid`) | failed/missing (`ImageFailureView`).
- **`ImageResultGrid`** — `<ul>` of `<li>`: `<img src alt={result.imageAlt(index, prompt)}>` + a `<a download>` per image, the placeholder caption when `backend` is `mock`/`local-motion`, and "Make another".
- **`ImageFailureView`** — `role="alert"`, `failure.title` or `failure.missing`, plus "Try again" and "Make another".
- **`imageSettings.test.ts`** — cost for standard×1 (5), high×4 (48), high×2 (24) and standard×3 (15); `blockedReason` for empty, whitespace, a real prompt and unavailable options; `deriveImagePhase` for both options states and **every** job phase.

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

 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests) 15ms
 ✓ src/features/explore/recreateHref.test.ts (4 tests) 9ms
 ✓ src/features/image-create/imageSettings.test.ts (3 tests) 11ms
 ✓ src/features/explore/groupPresetsByCategory.test.ts (6 tests) 13ms
 ✓ src/features/create-video/imageFileRules.test.ts (4 tests) 9ms
 ✓ src/features/create-video/elapsedTime.test.ts (3 tests) 11ms
 ✓ src/features/library/formatCreatedAt.test.ts (4 tests) 13ms
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests) 18ms
 ✓ src/api/jobStatusWatcher.test.ts (9 tests) 46ms

 Test Files  9 passed (9)
      Tests  60 passed (60)
   Start at  23:11:28
   Duration  508ms (transform 60%, import 24%, tests 9%, worker 7%)

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
dist/assets/index-Sa38Dsze.css   27.78 kB │ gzip:   5.82 kB
dist/assets/index-Dom_e5bA.js   341.73 kB │ gzip: 105.28 kB

✓ built in 334ms
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

=== T-009-6 verify: all steps exit 0 ===
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Acceptance self-checks
- **One `h1`**: `grep -c '<h1'` → `CreateImagePage.tsx` 1, every other file 0.
- **No user-visible string literal in a `.tsx`**: every text node is `{imageCreateCopy…}` or job data. (A naive `grep -E '>[^<>{]*[A-Za-z]'` only flags `=> void` inside arrow type declarations and `onChange={(event) => …}`, i.e. code, not copy.)
- **No colour-only state**: the cost is in the button label, the balance and every error are text; `role="status"` ×2 (progress, ready announcement), `role="alert"` ×2 (submit error, failure view), `aria-busy="true"` ×1.
- **`ui/` reused, nothing re-implemented**: `Button`, `ButtonLink`, `EmptyState`, `buttonStyles`.
- **File sizes**: largest is `ImageStage.tsx` 97, then `ImageComposer.tsx` ~140; every one is far under 200 and every function is ≤ 40 lines (`npm run lint` enforces both).
- **Type-checked while unreachable**: `tsc -b` includes `src/**`, so all ten files are checked even though `App.tsx` does not import the page yet (T-009-7).

## Open issues / guesses / things skipped
- **Sub-components live inside the six listed files, not in new files.** `max-lines-per-function: 40` (and `complexity: 8` on `ImageStage`) made the first drafts fail lint (57/45/57 lines, complexity 9). The brief's Allowed list and the design's Files table name exactly six `.tsx` files, so rather than invent `PromptField.tsx`/`GenerateSection.tsx`/… I extracted the pieces as **non-exported** components in the same file. The design's component tree already names `PromptField` and `GenerateSection`, so this matches the intended structure; it does bend STANDARDS' "one component per file" — flagging it for the reviewer.
- **`ImageResultGrid` gained an `onMakeAnother` prop** that the design's props table omits, because the brief requires the "Make another" action to live in the grid.
- **`ImageStagePhase` was added** (`"options-loading" | "options-error" | ImagePhase`): the brief requires the stage to render the options loading/error states, but the frozen `ImagePhase` union has no members for them. `deriveImagePhase` maps `(optionsStatus, jobPhase)` onto it, which is what its tests cover.
- **Copy gap: `network` and `invalid` submit errors have no dedicated string.** The Copy table only defines `generate.sessionError`. The composer shows `sessionError` for a session failure and falls back to `states.optionsError.body` ("Check your connection and try again.") for the other two — correct for a network failure, approximate for a 422. A `generate.invalid`/`generate.network` pair would remove the approximation; that is T-009-2's/design's call, not mine to invent.
- **The empty-`image_urls`-while-`succeeded` case is handled in `ImageStage`** (it renders `ImageFailureView`) rather than inside the grid; behaviour is the same as the brief describes, just at the level that owns `onRetry`.
- **`maxLength` uses a named constant** `MAX_PROMPT_LENGTH = 500` rather than the literal `500` — same value, and it keeps the magic number out of the JSX.
- **No DOM tests**: vitest runs in the Node environment here (no jsdom), so the components are covered by `tsc -b`/lint and the pure helpers by the 3 new tests; a browser pass on `/create/image` needs T-009-7 first.
- **The image API is not in this tree yet** (T-009-1/3/4/5), so the page compiles against the frozen contract but cannot complete a real generation until those land.

## Proposed STATUS.md line (WORKS)
| Create image UI: `/create/image` content — labelled prompt (500 max + counter), aspect/quality/count chips driven by the options payload, a Generate button showing the computed cost before submitting (disabled with a text reason while the prompt is empty), balance line, 402 balance/required line + "Get credits"; stage states options-loading/error → submitting/queued/running (`role="status"`) → grid of `count` images with descriptive `alt` + Download + placeholder caption, or the failure view (`role="alert"`); every string from `imageCreateCopy`, 3 new pure-helper tests | `apps/web/src/features/image-create/**` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` → lint/tsc clean, 60 tests (3 new), 109 modules, 0 violations (full output in `docs/tasks/T-009-6/report.md`) | 2026-09-13 17:41 |
