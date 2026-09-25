# Brief T-010-9: The Sequence tab (strip, transitions, music, eligibility, render)

**Role:** implementer · **Suggested model:** medium/strong · **Depends on:** T-010-3 and T-010-7 merged · **Wave:** W3

## Start here (any harness)
1. `scripts/task claim T-010-9 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md` § Web, **`DESIGN.md`** §4 ("Sequence strip") and §8, and spec 010 AC-12, AC-13, AC-14, AC-16 and AC-17.
3. Read `api/studioContracts.ts` (**`SequenceComposerProps` and `SequenceDraftControls` are your interface**), `features/studio/ComposerTabs.tsx` and `features/studio/useSequenceDraft.ts`.
4. Read `api/imageJobs.ts` and `api/library.ts` for the API-call pattern (`apiClient` plus `useGuestSessionRunner`), and `features/create-video/useImageUpload.ts` plus `putFileWithProgress.ts` for the upload flow (`POST /uploads` → PUT → complete).
5. Questions: `scripts/task say T-010-9 QUESTION "…"`.

## Goal
In the Sequence tab you arrange 2–6 of your clips, choose a transition per cut, optionally drop in music, and press **Render · 1 credit**. The job then appears on the stage and in the rail like any other job.

## Allowed files (touch nothing else)
- `apps/web/src/features/sequence/*` (new)
- `apps/web/src/api/sequenceJobs.ts` (new): `createSequenceJob(run, body)` → typed result, for `POST /api/v1/sequence-jobs`
- `apps/web/src/api/audioUpload.ts` (new): `useAudioUpload(session)` → `{ state, pickAudio(file), clearAudio() }`, reusing the existing upload endpoints with the audio content types
- `apps/web/src/api/putFileWithProgress.ts` (new): a **copy** of `features/create-video/putFileWithProgress.ts`, because a feature may not import another feature's internals. T-010-8 deletes the old copy.
- tests for the above
- `apps/web/src/features/studio/ComposerTabs.tsx`: **only** replace `SequencePlaceholder` with `<SequenceComposer … />`
- `docs/tasks/T-010-9/report.md`, `docs/verification/T-010-9/*.png`

## The change
1. **`SequenceComposer({ onJobStarted, sequence, libraryItems })`:**
   - **The strip:** `draft.clips` as slots (the poster thumbnail, and a remove button with `aria-label="Remove shot 2"`). While there are fewer than 2 clips, show trailing dashed empty slots reading "Add a clip from the rail". The strip scrolls horizontally inside itself.
   - **Reordering:** drag-and-drop with the native HTML5 DnD API (no new dependency), **plus** keyboard-accessible "Move left"/"Move right" buttons on each slot.
   - **Transition chips** between slots: click cycles `cut → crossfade → fade_black → cut`. Labels are mono `CUT` / `XFADE` / `FADE`, with `aria-label="Transition before shot 3: Crossfade"`. Each calls `setTransition`.
   - **The clip picker:** a compact row of the eligible clips from `libraryItems`, each with an "Add" button. The rail's "Add to sequence" on the stage does the same through the shared draft.
   - **Eligibility (AC-13):** only `kind === "video"` and `status === "succeeded"` with a `video_url`.
     - Aspect comes from the poster image's `naturalWidth/naturalHeight`, loaded once per clip and cached in a hook (`useClipAspects`).
     - After the first clip, a clip whose aspect differs by more than 0.02 is shown disabled with the text "Different shape: 9:16" (format the ratio simply).
   - **Music:** a drop zone or file button accepting `.mp3,.m4a,.wav`, up to 10 MB. Upload with `useAudioUpload`, then `setAudio({assetId, name})`. Show the file name and a Remove button. Validation errors appear inline in `danger`. Without music, show the muted line "Silent. Clip audio is not used."
   - **The total:** the sum of 5 s per clip minus 0.5 s per non-cut transition, shown in mono (`0:14`) and labelled "about". Clips are about 5 s each, and the server reports the real length.
   - **Render · 1 credit:**
     - Disabled with a visible reason when there are fewer than 2 clips or music is still uploading.
     - It posts `{clips:[{job_id, transition_in}], audio_asset_id?, idempotency_key: crypto.randomUUID()}`.
     - A 202 → `onJobStarted(id)`, then `clearDraft()`.
     - A 402 → `useCreditsPopover().openCredits()`.
     - A 404/422 → inline "One of these clips can't be used any more. Remove it and try again."
     - A 429 → the limit message.
2. **Copy** in `features/sequence/sequenceCopy.ts`, in the DESIGN.md §9 voice (run `no-ai-slop` Detect mode).
3. **Tests:**
   - Transition chip cycling.
   - Render disabled with fewer than 2 clips.
   - An ineligible (different aspect) clip is disabled with its reason. Mock the image load.
   - The payload shape posted, with and without audio.
   - Audio over 10 MB or the wrong type is rejected before any upload.

## Acceptance checks
- [ ] AC-12, AC-13, AC-14 (client side), AC-16 (the job appears on the stage via `onJobStarted`) and AC-17 (client validation)
- [ ] Fully keyboard-operable: add, move, remove, change transition, render
- [ ] No new npm dependency
- [ ] Every file ≤ 200 lines; components render and hooks own the data
- [ ] lint, test, typecheck, build and check-standards pass

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build
```
If the local API and worker are running (`docker compose up`), render a real 2-clip sequence and save a screenshot of the strip and of the stage result to `docs/verification/T-010-9/`.

## Out of scope
- The stitch worker (T-010-6), the sequence API (T-010-3), the stage and rail (T-010-7).

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-9`
2. `scripts/task submit T-010-9 --as <you> [--transcript <file>]`
