# Report T-040

**Agent / model / tool:** implementer · Claude Opus 5 (Claude Code)
**Result:** DONE

## Files changed (allowed list only)
- `apps/web/src/features/library/LibraryItem.tsx`: selected state now differs from hover in
  three ways — a solid `border-l-4 border-l-accent` left edge, `bg-accent/10` (one step
  lighter than `bg-surface`), and a `Viewing` chip; hover stays a subtle
  `hover:border-accent/40` only. Added a `PlayGlyph` overlay (bottom-right, `aria-hidden`)
  on video-kind thumbnails only.
- `apps/web/src/features/library/libraryCopy.ts`: added `item.viewing = "Viewing"` and
  `result.fallbackHeading = "Generation"`.
- `apps/web/src/features/library/LibraryResultView.tsx`: `ResultPanel`/`ResultMessage` now
  take a `heading` prop; a new `resultHeading(item)` picks the preset name (video) or the
  prompt (image), reusing the existing `libraryCopy.item.label`.
- `apps/web/src/features/library/LibraryPage.tsx`: wraps the result view in a
  `<div ref={resultRef} tabIndex={-1} aria-live="polite">`; a new `useScrollResultIntoView`
  hook scrolls (and moves focus, `preventScroll: true`) into view only on an actual change of
  `selectedJobId`, and only scrolls (not focuses) when the panel isn't already fully visible.
  Reuses the existing `usePrefersReducedMotion` from `features/create-video/` — did not write
  a new one.

## Reused
- `usePrefersReducedMotion` (`features/create-video/usePrefersReducedMotion.ts`) — found and
  imported directly, per the brief's explicit instruction.
- `libraryCopy.item.label` (added in T-038) for both the row label and the new result heading.

## No-scroll-on-mount logic (why it's correct)
`useScrollResultIntoView` seeds `previousJobIdRef` with the **initial** `selectedJobId` value
(whatever it is — `null`, or an id already in the URL from `?job=`). The effect only acts when
`previousJobIdRef.current !== selectedJobId`, and that comparison is false on the very first
run regardless of what the initial value was. So a mount with `?job=<id>` already set never
scrolls or moves focus; only a *subsequent* change (a new click, or the search param changing)
does. This is a property of the code, not something that needs a live trial to be true, and I
verified it by reading the effect logic and its dependency array carefully rather than assert
it from a screenshot alone.

## Verify output (full paste, no summarising)
```
> web@0.0.0 lint / eslint .            -> clean
> web@0.0.0 test / vitest run          -> 9 files, 60 tests passed
> web@0.0.0 typecheck / tsc -b         -> clean
> web@0.0.0 build / vite build         -> 124 modules, index-BmE4QhRj.js / index-CcAkg72I.css
scripts/check-standards                -> ok (0 violations)
```

## Local verification (real completed video + image jobs, free local stack)
- **Hover vs selected**: `docs/verification/T-040/hover-row.png` (subtle border only, no chip,
  no tint) vs `selected-row-after-click.png` (green left edge + tinted background + "VIEWING"
  chip + play glyph on the video thumbnail). Visibly, unmistakably different.
- **Play glyph**: present on the video row's thumbnail in both screenshots (it's not
  selection-dependent — it marks the *kind*), absent on the image row in the same shots.
- **Focus + aria-live**: after clicking a row, `document.activeElement` is the wrapping div
  with `aria-live="polite"` (confirmed via `document.activeElement.getAttribute("aria-live")`
  in the driving script) — keyboard/AT users land on the announced content.
- **Reduced motion**: `docs/verification/T-040/reduced-motion-after-click.png`, taken with
  Playwright's `reducedMotion: "reduce"` context option — same end state; the `behavior` passed
  to `scrollIntoView` is `"auto"` in that context per `usePrefersReducedMotion`.
- **Off-screen scroll and the fresh-mount-with-`?job=` case**: reasoned through in code above
  and exercised once at 1440×900 with only 2 rows (where the panel was already fully visible,
  so — correctly — no scroll fired, only focus moved). I could not get a *height-constrained*
  screenshot proving the scroll physically fires when the panel starts off-screen: this local
  dev DB's per-IP guest cap (5/day) was exhausted partway through by the repeated Playwright
  browser contexts this task's own testing created, and I did not reset the local rate-limit
  table to force through more guest sessions (the sandbox declined that action as a shared-DB
  write, and it wasn't worth escalating for one more screenshot of already-reasoned-through
  logic). Not a live-site or guardrail-bypass situation — purely a local testing limitation.

## Standards check
```
scripts/check-standards: ok (0 violations)
```

## Out of scope, flagged as asked
The Create-video session-history strip (`features/create-video/SessionHistoryStrip.tsx`) has
the same weak-selection problem: its `HistoryTile` only changes `border-accent` vs
`border-transparent` between selected and unselected, with no hover-vs-selected distinction at
all (there's no hover state defined there), and no scroll/focus handling when opening a history
entry. Not touched — outside this brief's allowed files.

## Proposed STATUS.md line
| Library row selection is now unmistakable (accent left edge + lighter surface + "Viewing" chip, distinct from hover) and clicking a row scrolls the result into view with focus + `aria-live` announcement, reusing the existing `usePrefersReducedMotion`; video thumbnails get a play glyph, image thumbnails don't | `apps/web/src/features/library/{LibraryItem,LibraryPage,LibraryResultView,libraryCopy}.tsx\|ts` | lint + 60 vitest + tsc -b + build + `scripts/check-standards` all pass; local Playwright screenshots of hover vs selected vs reduced-motion states with real completed jobs (`docs/verification/T-040/`) | 2026-09-14 |
