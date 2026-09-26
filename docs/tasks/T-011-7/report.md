# Report T-011-7

**Agent:** sonnet-5@claude-code · **Role:** implementer (web) · **Result:** PARTIAL

Parts 1 (trim UI) and 2 (tool links) are done and verified. Part 3 (real showcase) is
not done: `docs/tasks/T-011-7/showcase.json` did not appear in the main checkout after
polling every 2 minutes for ~40 minutes (20 checks, all `NOT_FOUND`).

## Files changed
- `apps/web/src/api/studioContracts.ts`: `SequenceDraftClip` gains `durationMs`,
  `trimStartMs`, `trimEndMs`. `SequenceDraftControls` gains `setTrim(index, trimStartMs,
  trimEndMs)`; `addClip`'s param type now omits the three fields the draft fills in.
- `apps/web/src/features/sequence/sequenceDraftView.ts`: `DEFAULT_CLIP_DURATION_MS` (5000),
  `TRIM_STEP_MS` (500), `MIN_TRIMMED_MS` (1000), `clampTrim` (keeps start/end in bounds and
  at least 1 s apart), `formatTrimPoint`/`formatTrimRange` (mono `0:00.5-0:04.0` readout).
  `approximateTotalSeconds` now sums each clip's trimmed length instead of a flat 5 s.
  `toPayloadClips` sends the clip's real `trim_start_ms`/`trim_end_ms` (still `null` for
  `trim_end_ms` when the clip is untrimmed at its full known length, matching the API's
  "unset means full length" contract from T-011-6).
- `apps/web/src/features/sequence/TrimControls.tsx` (new): the two in/out steppers (four
  +/- buttons total, 0.5 s steps) plus the mono readout, under each clip slot.
- `apps/web/src/features/sequence/SequenceStrip.tsx`: `ClipSlot` takes the whole `clip` (not
  just `jobId`/`posterUrl`) and renders `TrimControls` below the frame.
- `apps/web/src/features/sequence/sequenceCopy.ts`: four new `strip.trim*` aria-label copies.
- `apps/web/src/features/sequence/ClipPicker.tsx`: `addClip` now passes
  `durationMs: item.duration_ms ?? DEFAULT_CLIP_DURATION_MS` (Library's real duration when
  known, else the 5 s default per the brief).
- `apps/web/src/features/studio/draftOps.ts`: `addClipToDraft` sets `trimStartMs: 0`,
  `trimEndMs: clip.durationMs` on every new clip (a stable, pure function, no draft closure).
  New `setClipTrim(draft, index, trimStartMs, trimEndMs)`, same shape as `setClipTransition`.
- `apps/web/src/features/studio/useSequenceDraft.ts`: new `setTrim` callback, a stable
  functional updater (`setDraft((prev) => setClipTrim(prev, ...))`), included in the
  memoised controls object and its dependency array.
- `apps/web/src/ui/AppShell.tsx`: top-bar `Studio` link now sits in a `<nav aria-label="Tools">`
  alongside a new `Face swap` link to `/studio?tab=faceswap`, same link styling as `Studio`.
- `apps/web/src/features/sequence/sequenceDraftView.test.ts`: `draftOf` fixture now carries
  `durationMs`/`trimStartMs`/`trimEndMs`; added tests for `clampTrim`, the trimmed total
  length, `formatTrimRange`, and a payload test asserting `toPayloadClips` includes the trim
  fields on a trimmed clip (hard-won lesson #2 from the brief).
- `apps/web/src/features/studio/draftOps.test.ts`: `CLIP` fixture gains `durationMs`; new
  `describe("sequence draft trim", ...)` block covering the default full-length trim and
  `setClipTrim` leaving other clips untouched.

## Files touched outside the brief's allowed list (flagged via QUESTION, not blocking)
- `apps/web/src/features/studio/StudioPage.tsx`: `onAddToSequence`'s call to `draft.addClip`
  needed the new required `durationMs` field to keep `typecheck`/`build` green (it wasn't in
  the "Allowed files" list). Mechanical, one line, same pattern the coordinator already
  approved for T-011-6's consumer fixes. Raised as `scripts/task say T-011-7 QUESTION` before
  making the change; did not stop, since a hard typecheck failure would have blocked all of
  parts 1-2 otherwise.

## Reused
- `SlotChrome`/`ClipSlot` layout and `SlotControls` pattern in `SequenceStrip.tsx`.
- `TransitionChip`'s stepper-button styling (mono, `bg-sunken`/`bg-surface`, `text-accent`
  hover) reused for `TrimStepButton`.
- `setClipTransition`'s "only touch this index" map pattern, reused verbatim for `setClipTrim`.
- The `useSequenceDraft` stable-functional-updater convention already in place for
  `removeClip`/`moveClip`/`setTransition`/`setAudio`.

## Verify: see `verify.log` (written by `scripts/task verify`, run from inside the worktree)
```
> web@0.0.0 lint
> eslint .

> web@0.0.0 test
> vitest run

 Test Files  21 passed (21)
      Tests  106 passed (106)

> web@0.0.0 typecheck
> tsc -b

> web@0.0.0 build
> tsc -b && vite build
built in 155ms

check-standards: ok (0 violations)
RESULT: PASS
```

## Standards check
```
check-standards: ok (0 violations)
```

## Acceptance checks
- AC-6 (trim UI): yes for the pure maths and the payload. Each slot has an in/out stepper
  pair in 0.5 s steps, a mono `0:00.5-0:04.0` readout, a 1 s minimum enforced by `clampTrim`,
  and the clip length source is the Library's `duration_ms` when present, else 5 s
  (`DEFAULT_CLIP_DURATION_MS`). The total readout (`approximateTotalSeconds`) uses the
  trimmed lengths. All draft updaters are stable functional updaters; none closes over
  `draft`.
- AC-7 tool links: yes. `Studio` and `Face swap` sit in the top bar; `Face swap` links to
  `/studio?tab=faceswap`.
- Real showcase: not done. `docs/tasks/T-011-7/showcase.json` never appeared in the main
  checkout during the ~40-minute poll (checked every 2 minutes, 20 checks). `webMedia.ts`,
  `StartStepMedia.tsx` and `StartSteps.tsx` are untouched, still on the placeholder/preset
  stand-ins.

## Open issues / guesses / things skipped
- Part 3 (real showcase row + start-page step media) is not implemented; `showcase.json`
  was never produced by the other session within the wait window. If it appears later, this
  task needs a follow-up (or a fresh T-011-7-b) to add `SHOWCASE_*` to `webMedia.ts` and wire
  the start page's step media and the 4-item showcase row per DESIGN.md section 5
  (2fr/1fr/1fr grid, no three equal cards).
- `StudioPage.tsx` was touched outside the brief's allowed-files list; see above. No other
  files outside the brief's list were changed.
- `TrimControls`'s four +/- buttons are visually dense at 120px wide (five items in one row);
  functionally correct and keyboard/aria-labelled, but a reviewer with more visual-design
  latitude may want to reflow this (e.g. two rows) - flagging rather than guessing further
  since DESIGN.md doesn't specify a stepper layout beyond "two small steppers."

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Sequence clip trim UI + tool links (web) | `apps/web/src/features/sequence/TrimControls.tsx`, `apps/web/src/ui/AppShell.tsx` | `scripts/task verify T-011-7` | 2026-09-26 |
