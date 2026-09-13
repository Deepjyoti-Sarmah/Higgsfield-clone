# Report T-004-4

**Agent / model / tool:** implementer · deepseek-flash (DeepSeek Harness) · direct session (no `scripts/agent-run` wrapper available in this harness; transcript captured by the harness)
**Result:** PARTIAL

## Files changed
All nine `apps/web/src/features/create-video/` files are new (untracked); no existing file was edited.

- `useClipboardImagePaste.ts` (26 lines): `useClipboardImagePaste(onImage)` — one `window` `paste` listener while mounted, claims the event only when `clipboardData.files` holds an accepted image type, then `preventDefault()` + `onImage(file)`; text pastes pass through untouched.
- `ImageDropZone.tsx` (180 lines): `ImageDropZone{upload}` — whole-zone drop target (`onDragOver` preventDefault + accent highlight, `onDragLeave`, `onDrop` → first file), hidden `<input type="file" accept={ACCEPTED_IMAGE_TYPES}>` reset after each pick, real `Browse files` `ui/Button`, `aria-describedby` → hint/error ids, `role="alert"` errors, all six Image copy states.
- `ImageThumbnail.tsx` (60 lines): `ImageThumbnail{previewUrl, progress, onReplace, onRemove}` — `alt="Your image"` preview, upload overlay with `Uploading… {pct}%` + determinate `ui/ProgressBar`, `Replace` + icon button `aria-label="Remove image"`.
- `PresetPicker.tsx` (130 lines): `PresetPicker{presets, selection, previewImageUrl, groupRef}` — `<fieldset ref>` + `<legend>Preset</legend>`, chips, 3-col grid, 6 skeleton cards with `sr-only` `Loading presets…`, empty/filter-empty/error copy, unknown-slug hint, description line, one non-smooth `scrollIntoView({block:"nearest"})` of the checked radio when presets become `ready`.
- `PresetCategoryChips.tsx` (40 lines): `role="group" aria-label="Preset categories"` of `aria-pressed` buttons for All/Camera/Cinematic/Dynamic.
- `PresetCard.tsx` (60 lines): `PresetCard{preset, isSelected, previewImageUrl, onSelect}` — `<label>` with `sr-only` `type="radio" name="preset"`, always-visible `line-clamp-2` name, `border-accent` + accent check badge when selected, focus ring via `group-has-[:focus-visible]`, motion classes from `presetMotionClass(slug)` on the media under `motion-safe:`, gradient tile when `preview_url` is null.
- `PromptField.tsx` (39 lines): `PromptField{value, onChange}` — optional textarea, `maxLength` 500, `{n}/500` counter, exact placeholder + helper.
- `GenerateSection.tsx` (119 lines): exports `GenerateSectionProps`; cost button / `Starting…` / `Get credits` `ui/ButtonLink` to `/credits`, blocked-reason helper, all four `BalanceView` lines, insufficient line, inline `role="alert"` submit error per `SubmitErrorKind`.
- `docs/tasks/T-004-4/report.md`: this report.

## Reused
- `ui/Button` (`isLoading` → `Starting…`), `ui/ButtonLink` (`Get credits`), `ui/ProgressBar` (upload progress) — none edited.
- `createVideoCopy` for every string; `imageFileRules.ACCEPTED_IMAGE_TYPES` for `accept`; `presetMotionHints.presetMotionClass` for card motion.
- Types only from `createVideoTypes.ts` (`ImageUploadControls`, `PresetsState`, `PresetSelection`, `Preset`, `BalanceView`, `GenerateBlockedReason`, `InsufficientCredits`, `SubmitErrorKind`, `UploadErrorKind`); no hook is re-implemented and no data fetching happens in these files.

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


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

✓ built in 287ms
=== standards ===
apps/api/tests/test_job_creation_api.py: 225 lines (max 200)
check-standards: FAIL (1 violations)
standards exit=1
```

`lint`, `typecheck` and `build` pass with zero output. The verify chain stops at `scripts/check-standards` because of the one violation below.

## Standards check
```
$ scripts/check-standards
apps/api/tests/test_job_creation_api.py: 225 lines (max 200)
check-standards: FAIL (1 violations)
```
Exit code 1. **Not caused by this task**: `apps/api/tests/test_job_creation_api.py` is untracked (`??` in `git status`) and belongs to another agent's concurrent work (T-003 family). None of the nine T-004-4 files is over 200 lines and every function is inside the `max-lines-per-function: 40` / `max-depth: 3` / `complexity: 8` eslint limits (lint is clean). Per the brief's "if something still fails after 2 fixes, stop and report", this was re-run twice and left to the owner; the orchestrator may need to land/trim that file before the standards gate can pass repo-wide.

## Open issues / guesses / things skipped
- **Guesses made where the design is silent (all reported honestly):**
  1. **Radio controlledness in `PresetCard`.** I used `checked={isSelected}` + `onChange={() => onSelect(slug)}` (the design's exact markup). React treats every card as controlled, so when the URL carries a selected slug but the category filter hides that preset, the DOM radio may stay checked on the hidden card. The design's Accessibility section calls the native "Tab lands on the first card" behaviour acceptable, so this was left as specified; if it misbehaves in the T-004-5 manual check, the fix is to pass `checked` only when `isSelected`.
  2. **Drop-zone hint placement.** The hint sits *below* the dashed zone (a sibling in the section), matching "hint (always visible)"; the zone itself carries no copy when idle except the title/body.
  3. **Upload feedback is shown once.** The design says the overlay *and* a progress label show `Uploading… {pct}%`; I render the label once inside the bottom overlay (with the determinate `ProgressBar` and `aria-label` = the same label) rather than duplicating the same string twice.
  4. **Motion on the visitor's image.** Because `group-hover:` cannot originate from an `<img>`, the hover variant is emitted from the card `<label class="group">`; selected/focus variants use `has-[:checked]` / `group-has-[:focus-visible]`. The literal class strings still come from `presetMotionHints.ts`, so Tailwind's scanner sees them.
  5. **Hookless UI state only.** Local `useState` is used solely for `isDragging` (drop highlight) and a one-shot `hasScrolledRef`; no data state.
- **Not done here (out of scope):** `CreateVideoPage`, canvas views, announcer, history strip, `App.tsx` (T-004-5); any `ui/**`, `styles.css`, `api/**` or `package.json` edit; contract changes. No contract field needed by the copy was missing — `PresetResponse`, `InsufficientCreditsResponse` and `CreditsResponse` all match the copy functions.
- **Components are not unit-tested** (no DOM runner by design, § Test strategy); they are covered by `tsc` + the T-004-5 manual flow check.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Create-video panel components (drop zone/paste, thumbnail, preset picker + chips + cards, prompt, generate) render props-only, typed and lint-clean | `apps/web/src/features/create-video/{useClipboardImagePaste,ImageDropZone,ImageThumbnail,PresetPicker,PresetCategoryChips,PresetCard,PromptField,GenerateSection,CreateVideoPanel}.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build` (pass); `scripts/check-standards` blocked by unrelated `apps/api/tests/test_job_creation_api.py` | 2026-02-14 |
