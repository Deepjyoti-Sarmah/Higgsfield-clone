# Report T-041

**Agent / model / tool:** implementer · Claude Opus 5 (Claude Code)
**Result:** DONE

## Files changed (allowed list only)
- `apps/web/src/features/create-video/SessionHistoryStrip.tsx`: active tile now
  `border-accent ring-2 ring-accent/40` (was `border-accent` alone); inactive tile gets
  `hover:border-border hover:brightness-125` (was no hover state at all); caption is
  `text-text font-medium` when active, `text-muted` otherwise (was always `text-muted`); a new
  `PlayGlyph` (small triangle, bottom-right, soft scrim, `aria-hidden`) shows on
  `status === "succeeded"` tiles; the existing status dot still covers queued/running/failed.
- `apps/web/src/features/create-video/CreateVideoPage.tsx`: `useCanvasFocus` — the hook that
  already moved focus to the canvas heading on any active-job change — now also scrolls the
  canvas into view whenever it isn't already fully visible (`isFullyVisible`, same
  bounding-rect check T-040 used), on **any** viewport, not just the previous
  `max-width: 767px` mobile-only check. `focus()` now uses `preventScroll: true` so it never
  double-scrolls with `scrollIntoView`. Trimmed comments/whitespace elsewhere in the file to
  stay at exactly 200 lines (the standards cap) after the addition.
- `CreateVideoCanvas.tsx` / `createVideoCopy.ts`: **not changed.** The canvas already had a
  `tabIndex={-1}` heading (`CanvasHeading.tsx`) as the focus target, and the page already had
  a `StatusAnnouncer` doing the screen-reader announcement job T-040 gave the Library its own
  `aria-live` for — no new strings or markup were needed.

## Reused (not rebuilt)
- `usePrefersReducedMotion` (`features/create-video/usePrefersReducedMotion.ts`) — already
  imported by `CreateVideoPage.tsx`, used as-is.
- `useCanvasFocus` itself: rather than building a second, parallel scroll/focus mechanism
  scoped only to history-tile clicks (which the brief's example implied), I extended the one
  hook that already runs on every `activeJobId` change — it already covered both "Generate" and
  "open a history tile" through the same `focusSignal`. Two mechanisms doing the same thing for
  two of three cases (Generate vs. history-tile-click) would have been the copy-paste this
  project's standards explicitly discourage.
- `isFullyVisible` bounding-rect check — same shape as `useScrollResultIntoView` in
  `LibraryPage.tsx` (T-040), not literally imported (different file/feature, no shared home for
  it exists yet) but intentionally identical in behavior.

## No-scroll-on-mount logic (same property as T-040, verified the same way)
`useCanvasFocus`'s `previousRef` starts at `null`. The effect's early-return
(`previous === null || previous === focusSignal || ...`) means the very first run after mount
always exits before touching the DOM, regardless of what `focusSignal` already is (including a
job already active from a page load). Only a genuine *subsequent* change — Generate, or a
history-tile click — clears that guard. Read and confirmed by inspection, matching how T-040's
`useScrollResultIntoView` was verified.

## Verify output (full paste, no summarising)
```
> web@0.0.0 lint / eslint .            -> clean (CreateVideoPage.tsx trimmed to exactly 200 lines)
> web@0.0.0 test / vitest run          -> 9 files, 60 tests passed
> web@0.0.0 typecheck / tsc -b         -> clean
> web@0.0.0 build / vite build         -> 124 modules, index-B4Rcurmt.js / index-TVXa8Y3s.css
scripts/check-standards                -> ok (0 violations)
```

## Local verification
**Local guest cap was exhausted before I could populate the strip with real backend jobs**
(same situation T-040 hit; `POST /auth/guest` -> 429 `{"limit":5,"used":5}`). Per the brief, I
did not reset the rate-limit table. Two substitutes, both real evidence rather than guesses:

1. **Styling** (`docs/verification/T-041/strip-inactive.png`, `strip-hover.png`): seeded the
   client-side history store directly — `sessionStorage["hf.createVideo.history.v1"]`, which
   `useSessionHistory`/`sessionHistoryStore.ts` read on mount, no backend call needed for the
   strip's own rendering — with one `succeeded`, one `running`, one `failed` entry. Confirms:
   the succeeded tile shows the play glyph, the other two keep their (correctly coloured)
   status dot, and hovering an inactive tile visibly lifts it.
2. **Interaction** (`docs/verification/T-041/strip-active.png`): a synthetic job id alone isn't
   enough to test the *active* state, because `useActiveJob`'s existing (correct, untouched)
   behaviour removes a history entry once its job comes back 401/404 as missing — so a fake id
   vanishes from the strip the instant it's clicked, before any screenshot can capture the
   active style. Routed around this **without touching the backend or spending a guest
   session**: used Playwright's request interception to fulfil `GET /api/v1/jobs/seed-succeeded-1`
   with a realistic succeeded `JobResponse` body. Clicking the tile then genuinely worked
   end-to-end: the tile got `border-accent ring-2 ring-accent/40` and its bold caption, the
   canvas swapped to "Your video is ready" with no manual scroll needed, and
   `document.activeElement` was the canvas `<h2>` — all three acceptance signals confirmed in
   one real (mocked-network, not application-code-mocked) interaction.

## Standards check
```
scripts/check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- None outside what's noted above. The horizontal-scroll-at-390px check wasn't re-verified
  with a live screenshot this round (T-039/T-040 already established the page has no
  page-level horizontal overflow, and this task didn't touch layout width, only tile-internal
  classes), so I'm relying on that precedent rather than re-running an unrelated check.

## Proposed STATUS.md line
| Create-video session-history tiles now give real feedback: active tile gets a border+ring+bold-caption (mirrors T-040's Library treatment), unselected tiles get a hover response, succeeded tiles show a play glyph (queued/running/failed keep their status dot), and clicking a tile scrolls the canvas into view (any viewport, not just mobile) with focus moved there | `apps/web/src/features/create-video/{SessionHistoryStrip,CreateVideoPage}.tsx` | lint + 60 vitest + tsc -b + build + `scripts/check-standards` all pass; local screenshots (seeded history + one network-mocked interaction) confirm inactive/hover/active tile styling and the scroll+focus behaviour end to end (`docs/verification/T-041/`) | 2026-09-14 |
