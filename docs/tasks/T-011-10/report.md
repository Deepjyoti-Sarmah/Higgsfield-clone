# Report T-011-10

**Agent:** sonnet-5@claude-code · **Role:** implementer (web) · **Result:** DONE

## Findings and root causes

### F1 — chosen aspect ratio ignored
Root cause: `ImageSettingsRow` called its own `useStillSettings()` hook instead of receiving
the composer's settings as a prop. `StillComposer` also calls `useStillSettings()` and holds
a separate `settingsState`. That means the chips the user clicked wrote into a settings
object that only `ImageSettingsRow` ever saw — `StillComposer.settingsState` (the one
actually sent by `submit(prompt, settingsState.settings)`) always stayed at
`DEFAULT_IMAGE_SETTINGS`. `stillJobBody`/`submitStill` already forward whatever settings
they're given correctly; the request body was never wrong once fed the real selection.
Fix: `ImageSettingsRow` now takes `settings: ImageSettingsControls` as a prop, and
`StillComposer` passes its own `settingsState` down, so there is exactly one seed of truth
for the composer's settings (per the "hold seeds in the composer's own state" rule).

### F2 — face-swap results have no "Animate this"
Root cause: `StageActions`' `StillActions` gated on `item.kind !== "image"`, excluding the
`faceswap` kind even though a succeeded face-swap item has the same `images[]` shape as a
still. Fix: gate on `item.kind !== "image" && item.kind !== "faceswap"`.

### F3 — stage didn't show "Use as face swap target" until a `?item=` reload
Root cause (best-effort, not reproduced live in this session — matches the F3 report's own
"not reproduced further"): `StageActions`'s visibility is driven entirely by the Library
snapshot's `item.status` (`StudioStage`'s `isTerminal` check), which only updates once
`StudioPage`'s `reloadLibrary()` runs. That reload is triggered from a single place: the
per-job SSE/poll watcher (`StageProgress` → `useJobEvents` → `onSettled`) calling back when
it observes a terminal status. If that one callback is ever missed — e.g. the browser's
per-origin `EventSource` cap (6) is hit while other jobs' streams from earlier in the
session are still open, so the new stream never opens and the poll fallback that would
normally catch a stream failure never gets a chance to start — there is no independent way
for the Library to notice the job finished, so the stage is stuck showing the old snapshot
indefinitely, exactly as reported (until a full reload remounts everything and fetches
fresh state). The watcher/SSE code lives in `apps/web/src/api/*`, outside this brief's
allowed files, so the fix here is a self-healing backstop inside `StudioPage`
(`useLibraryHealPoll`): while the selected item is `queued`/`running`, poll
`reloadLibrary()` every 5s regardless of the primary watcher's state, so a missed terminal
event heals itself within one poll interval instead of never. I could not force-reproduce
the missed-callback condition locally (would need many concurrent live jobs), so I can't
prove this is *the* root cause with certainty, only that it is a real single point of
failure in the code as written, and the fix is safe either way.

### F4 — credits popover ignores Escape
Root cause: the Escape handler was a React `onKeyDown` on the wrapping `<div>`, so it only
fires while the DOM event is still bubbling through that div's subtree. Functionally this
mostly works, but nothing ever returned focus to the trigger button afterwards — the
`<button>` and the popover's own content are siblings, and once `isOpen` flips to false the
`PopoverSurface` (and whatever inside it currently held focus) unmounts, and the browser
drops focus to `<body>` instead of the invoking control, which is the acceptance
requirement in DESIGN.md §4. Fix: replaced the bubbled `onKeyDown` with a `document`
`keydown` listener scoped to `isOpen` (robust regardless of where focus is inside the
dialog) that calls `closeCredits()` and then `buttonRef.current?.focus()`.

### F5 — share caption says "1 stills"
Root cause: `shareMeta` in `shareCopy.ts` used a hardcoded `` `${count} stills` `` with no
singular/plural branch. Fix: `` `${count} still${count === 1 ? "" : "s"}` ``, covering both
`image` and `faceswap` kinds (the same branch handles both).

## Files changed
- `apps/web/src/features/image-create/ImageSettingsRow.tsx`: takes `settings` as a prop instead of creating its own
- `apps/web/src/features/image-create/StillComposer.tsx`: passes its `settingsState` into `ImageSettingsRow`
- `apps/web/src/features/studio/StageActions.tsx`: treat `faceswap` like `image` for still-style actions
- `apps/web/src/features/studio/StudioPage.tsx`: added `useLibraryHealPoll` backstop so a missed terminal event self-heals
- `apps/web/src/features/credits/CreditsButton.tsx`: `useEscapeClose` (document listener) closes the popover and returns focus to the trigger button
- `apps/web/src/features/share/shareCopy.ts`: pluralise "still"/"stills" in `shareMeta`
- `apps/web/src/features/share/shareMeta.test.ts`: regression test for the singular case (image and faceswap)

## Reused
- Existing `stillJobBody`/`submitStill` (already correct — F1 was a wiring bug, not a body-builder bug)
- Existing `useStillSettings` hook, now used once per composer instance as intended

## Verify
See `verify.log`. All four steps passed: lint (0 errors after extracting `useLibraryHealPoll`
to keep `useStudioPanel` under the 40-line function limit), 107/107 tests, `tsc -b` clean,
`vite build` clean.

## Standards check
`scripts/check-standards` is run as part of `scripts/task verify`; see `verify.log`.

## Open issues / guesses / things skipped
- F1 has no new pure-logic test: the bug was in component wiring (which settings object gets
  read), not in a pure function — `stillJobBody`'s existing test already covered the body
  shape correctly. TypeScript now enforces the wiring (the prop is required), and the
  existing `stillSubmit.test.ts` still passes unchanged.
- F3's root cause is a reasoned best guess, not a live-reproduced one (I did not run many
  concurrent live jobs against Railway to force the EventSource cap). The fix is a
  defensive backstop that is safe and low-cost regardless of the exact cause, but the
  underlying watcher code (`apps/web/src/api/jobStatusWatcher.ts`, `useJobEvents.ts`) is
  outside this brief's allowed files, so if the real cause turns out to be inside that
  layer, a follow-up task should own it.
- No live/Playwright re-verification was run against Railway (not in scope for this brief;
  only the local `lint && test && typecheck && build` verify command was run).

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| T-011-10: fixed F1-F5 from T-011-8 live findings (aspect ratio wiring, face-swap animate/target actions, stage refresh backstop, credits popover Escape, share caption pluralisation) | `apps/web/src/features/{image-create,studio,credits,share}` | `npm --prefix apps/web run lint && test && typecheck && build` | 2026-09-26 |
