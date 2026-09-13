# Brief T-004-4: Panel components — drop zone, thumbnail, preset picker, prompt, generate

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/004-create-video/spec.md` (AC-1 panel order, AC-2 drop/browse/paste, AC-3 preset grid + chips + selected state, AC-4 cost + balance + "Get credits")
- Design: `docs/specs/004-create-video/design.md` sections **Component tree** + **Props**, **Every UI state with exact copy** (Page + panel, Image, Preset, Prompt, Generate), **Accessibility** (drop zone, paste, focus after upload, preset keyboard selection), **Preset card visuals** (motion hints), **Files**
- Contract: `packages/contracts/openapi.json`, schema `PresetResponse` (`slug`, `name`, `description`, `category`, `credit_cost`, `preview_url`) and `InsufficientCreditsResponse` (`balance`, `required`)
- Types/copy/primitives you import (do not edit): `createVideoTypes.ts`, `createVideoCopy.ts`, `imageFileRules.ts`, `presetMotionHints.ts`, `ui/{Button,ButtonLink,ProgressBar}.tsx` from T-004-1
- Existing patterns: `apps/web/src/ui/Button.tsx` (`isLoading` → "Starting…"), `apps/web/src/styles.css` tokens

## Goal
Build the whole left control panel as small, pure-render components with fixed props: a drop zone that accepts drag & drop, browse and clipboard paste with inline errors; a thumbnail with upload overlay, Replace and Remove; a preset fieldset of keyboard-operable radio cards with category chips, loading/empty/error/unknown-slug states and motion previews on the visitor's own image; the optional prompt field with its counter; and the generate section with the real cost, the balance line, the blocked-reason helper, the "Get credits" link and the inline submit errors. No data fetching lives in these files — props only.

## Allowed files (touch nothing else)
- `apps/web/src/features/create-video/useClipboardImagePaste.ts`
- `apps/web/src/features/create-video/CreateVideoPanel.tsx`
- `apps/web/src/features/create-video/ImageDropZone.tsx`
- `apps/web/src/features/create-video/ImageThumbnail.tsx`
- `apps/web/src/features/create-video/PresetPicker.tsx`
- `apps/web/src/features/create-video/PresetCategoryChips.tsx`
- `apps/web/src/features/create-video/PresetCard.tsx`
- `apps/web/src/features/create-video/PromptField.tsx`
- `apps/web/src/features/create-video/GenerateSection.tsx`
- `docs/tasks/T-004-4/report.md`

`GenerateSectionProps` is defined and exported by `GenerateSection.tsx`; `CreateVideoPanel` imports it. Do not create any other file.

## Must reuse
- `ui/Button` (with `isLoading`), `ui/ButtonLink` (the "Get credits" link; never nest a button in a `Link`), `ui/ProgressBar` (upload progress + thumbnail overlay).
- `imageFileRules.ACCEPTED_IMAGE_TYPES` for the file input's `accept` attribute; `createVideoCopy` for every string; `presetMotionClass(slug)` for the card preview classes.
- Tailwind tokens in `styles.css` only; headings inherit the global display-font rule. Errors use `text-red-400`; the selected state uses `border-accent`.
- The exact prop contract from the design's **Props** table: `ImageDropZone{upload}`, `ImageThumbnail{previewUrl, progress, onReplace, onRemove}`, `PresetPicker{presets, selection, previewImageUrl, groupRef}`, `PresetCategoryChips{value, onChange}`, `PresetCard{preset, isSelected, previewImageUrl, onSelect}`, `PromptField{value, onChange}`, `GenerateSection{selectedPreset, blockedReason, isSubmitting, balance, insufficient, submitError, onGenerate}`.

## Acceptance checks
- [ ] `useClipboardImagePaste(onImage)` adds one `window` `paste` listener while mounted, acts only when `clipboardData.files` contains an image, calls `preventDefault()` + `onImage(file)`, and leaves text pastes (into the prompt) untouched.
- [ ] `ImageDropZone`: the whole zone is a drop target (`onDragOver` preventDefault + highlight, `onDragLeave`, `onDrop` → first file); a real `Browse files` button drives a hidden `<input type="file">` whose `value` resets after each pick; `aria-describedby` points at the hint + error ids; errors are `role="alert"`; the copy matches the Image table exactly (`Add an image`, `Drop it here, browse, or paste from your clipboard.`, `Drop to upload`, `Uploading… {pct}%`, `Upload failed…`, `Couldn't start a session…`, `Upload didn't finish…`).
- [ ] `ImageThumbnail` shows the ready preview (`alt="Your image"`) with `Replace` and an icon button `aria-label="Remove image"`, and the determinate `ui/ProgressBar` + `Uploading… {pct}%` while uploading.
- [ ] `PresetPicker` renders `<fieldset ref={groupRef}>` + `<legend>` `Preset`, the chips group, 6 skeleton cards with visually hidden `Loading presets…`, the empty/filter-empty/error text, the `isUnknownSlug` hint, and the description line (`Pick a camera move for your video.` / `{name}: {description}`). Once, when presets are `ready` with a selection, it scrolls the checked card into view (`block: "nearest"`, no smooth) without moving focus.
- [ ] `PresetCard` is a `<label>` wrapping a `sr-only` `type="radio" name="preset"`; names are always visible (`line-clamp-2`); selected state is `has-[:checked]:border-accent` + an accent check badge; focus ring via `has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent`; motion classes come from `presetMotionHints` and run only on hover/focus/selected under `motion-safe:`; `preview_url` null → the visitor's `previewImageUrl` inside an `aspect-square overflow-hidden` tile, else a neutral gradient.
- [ ] `PromptField` is an optional textarea with `maxLength` 500, the counter `{n}/500`, the exact placeholder and the helper `Some presets ignore the prompt.`
- [ ] `GenerateSection` shows `Generate · {cost} credits` (or plain `Generate` with no preset), `Starting…` while submitting, the exact blocked-reason helper per `blockedReason`, the balance line per `BalanceView` (`Balance: {n} credits` / `Balance: …` / `Balance unavailable` / `Free credits to start. No sign-up needed.`), turns into the `Get credits` `ButtonLink` to `/credits` plus `You have {balance} credits. This video needs {required}.` for `insufficient`, and renders the inline submit error per `SubmitErrorKind`.
- [ ] `CreateVideoPanel` renders sections in the order Image → Preset → Prompt → Generate with the `h1` `Create video`, the section labels, and the focus-after-upload effect exactly as designed (only when `document.activeElement` is inside the drop zone; move focus to the checked radio in `groupRef`, else the first radio).
- [ ] No file over 200 lines, no function over 40 lines, complexity ≤ 8 (`npm run lint`); no `useState`/fetch in a component that a hook owns.

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any hook (T-004-2/3) and every canvas/page file (T-004-5): no `CreateVideoPage`, canvas views, announcer, history strip, `App.tsx`.
- `apps/web/src/ui/**` edits, `apps/web/src/styles.css`, `apps/web/src/api/**`, `apps/web/package.json`.
- Contract/API changes. If a field the copy needs is missing from `openapi.json`, stop and write it in the report's open issues.

## Report
Write `docs/tasks/T-004-4/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
