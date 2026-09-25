# Brief T-010-8: Still and Clip composers (compact, "Animate this" seeding, honest errors)

**Role:** implementer · **Suggested model:** medium · **Depends on:** T-010-4 and T-010-7 merged · **Wave:** W4

## Start here (any harness)
1. `scripts/task claim T-010-8 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md` § Web, **`DESIGN.md`** §4 (composer, inputs, buttons) and §9 (voice), and spec 010 AC-8, AC-9, AC-10 and AC-11.
3. Read `api/studioContracts.ts` and `features/studio/ComposerTabs.tsx` (from T-010-7). **`ComposerProps` and `ClipComposerProps` are your interface.**
4. Read all of `features/create-video/` and `features/image-create/`. Separate the **hooks** (you keep them) from the **views** (you rebuild or remove them).
5. Questions: `scripts/task say T-010-8 QUESTION "…"`.

## Goal
The Still and Clip tabs are compact composers that only **collect input and start a job**. Progress and results now live on the studio stage, which T-010-7 built. "Animate this" hands a generated still to the Clip composer as its input, with no upload.

## Allowed files (touch nothing else)
- `apps/web/src/features/image-create/*`
- `apps/web/src/features/create-video/*`
- `apps/web/src/features/studio/ComposerTabs.tsx`: **only** swap the Still and Clip imports and props for `StillComposer`/`ClipComposer`
- `apps/web/src/styles.css`: **only** remove the `--animate-hf-*` alias tokens once nothing uses them
- `docs/tasks/T-010-8/report.md`, `docs/verification/T-010-8/*.png`

## The change
1. **`StillComposer({ onJobStarted })`** in `features/image-create/StillComposer.tsx`:
   - A prompt (1–500 characters), then aspect, quality and count from `useImageOptions`.
   - A primary button showing the live cost in mono (`Generate · 20 credits`), disabled with a visible text reason when the prompt is empty or options are loading.
   - On a 202 → `onJobStarted(id)` and clear the prompt.
   - On a 402 → `useCreditsPopover().openCredits()` plus an inline line with `balance`/`required`.
   - On a 429 → the inline limit message.
   - Reuse `useImageJob`'s submit logic. If the hook bundles watching, which the composer no longer needs, use only its create path, or extract the create call into `imageJobs` helpers **within this feature** without editing `api/`.
2. **`ClipComposer({ onJobStarted, seedImage, onSeedConsumed })`** in `features/create-video/ClipComposer.tsx`:
   - The input image: drop, pick or paste (reuse `useImageUpload`, `useClipboardImagePaste` and `ImageDropZone`), or a **seeded still**.
   - With a `seedImage`: show its thumbnail labelled "From your still", and use `seedImage.assetId` as `input_asset_id` directly. No upload. Call `onSeedConsumed()` once it's adopted. The user can replace it by dropping another image.
   - Then the prompt (optional) and the motion preset (reuse `usePresetSelection`, `PresetPicker` and chip styling). Presets deep-linked with `?preset=slug` still preselect.
   - `Generate · N credits`, with the same 402/429 handling as Still.
3. **Remove the views** that duplicated the stage:
   - `CreateVideoPage`, `CreateVideoCanvas`, `ResultView`, `JobProgressView`, `FailureView`, `StatusSteps`, `SessionHistoryStrip`, `HowItWorks`, `HowItWorksStep`, `CanvasHeading`
   - their image-create equivalents: `CreateImagePage`, `ImageStage`, `ImageResultGrid`, `ImageProgressView`, `ImageFailureView`
   - any hooks and tests used **only** by removed views (e.g. `sessionHistoryStore`, `canvasPhase`)

   List every deleted file in the report, with one line on why it's unused. **Keep** every hook that a composer still uses, along with its tests.
4. **Shared copies:** delete the create-video copies of `usePrefersReducedMotion` and `putFileWithProgress` (with their tests, if any). Import `ui/usePrefersReducedMotion` and `api/putFileWithProgress` instead (created by T-010-7 and T-010-9).
5. **Motion tokens:** switch `presetMotionHints.ts` to the `animate-motion-*` names, then delete the `--animate-hf-*` aliases from `styles.css`.
6. **Copy:** rewrite `createVideoCopy.ts` and `imageCreateCopy.ts` in the DESIGN.md §9 voice. No "Higgsfield". Run the `no-ai-slop` skill in Detect mode over both, and paste its findings and your fixes in the report.
7. **`ComposerTabs.tsx`:** mount `<StillComposer onJobStarted={…} />` and `<ClipComposer onJobStarted={…} seedImage={…} onSeedConsumed={…} />`.
8. **Tests:**
   - `ClipComposer` with a `seedImage` submits `input_asset_id = seed.assetId` without calling upload.
   - `StillComposer`'s Generate is disabled with its reason on an empty prompt.
   - A 402 calls `openCredits`.
   - Mock the API the way existing tests do.

## Acceptance checks
- [ ] AC-8, AC-9 and AC-10 hold end to end in the studio, with results on the stage
- [ ] `grep -rniE "higgsfield|hf-" apps/web/src` returns nothing
- [ ] No hook test deleted unless its hook was deleted as unused, as listed in the report
- [ ] Mobile 390px: the fields stack and there's no horizontal scroll
- [ ] lint, test, typecheck, build and check-standards pass

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && ! grep -rniE "higgsfield|animate-hf|hf-motion" apps/web/src
```

## Out of scope
- The stage and rail (T-010-7), sequences (T-010-9), the credits popover (T-010-11), any backend.

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-8`
2. `scripts/task submit T-010-8 --as <you> [--transcript <file>]`
