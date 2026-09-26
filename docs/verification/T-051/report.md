# T-051 studio spacing, density and alignment

Date: 2026-09-26. Orchestrator: deepseek-flash.

## The problem (measured on the live studio)

`<main>` carried the marketing shell's padding `40px 24px`, so the studio was inset from the top
and sides. The rail's "Your work" header sat 40px under the nav with a 24px left gap. The rail rows
used 64px thumbnails and a full date stamp (`26 Sep 2026, 0...`) that truncated. The composer
column mixed 16px and 24px gutters, and the studio still showed the site footer.

Measured before: `main.padding = "40px 24px"`, `aside = (24, 96)`.

## What changed

1. **Full-bleed studio.** `App.tsx` marks `/studio` full-bleed and footer-less; `AppShell` renders
   `main` as `flex min-h-0 flex-1 flex-col` with no padding, and `StudioPage` fills it.
   Measured after: `main.padding = "0px"`, `aside = (0, 56)`, rail 288px.
2. **Denser, aligned rail.** 56px thumbnails (DESIGN.md §4), 16px gutters, the per-row stamp is now
   the time only (`formatCreatedTime`) because the day heading already gives the date, the kind badge
   shares a 16px line-height with the mono meta, filter chips are tighter with tabular numbers, and
   the count reads at 12px.
3. **Consistent gutters.** Flow strip and explainer moved to `sm:px-6`, matching the composer body
   and the top bar's 24px gutter.
4. **Unified chrome.** The desktop rail now sits on `surface`, the same as the mobile drawer and the
   composer, so the rail header and rows are one panel.

## Verification

- `npm --prefix apps/web run lint` clean; `test` **134 passed**; `build` ok; `scripts/check-standards` ok.
- Layout measured with `docs/verification/T-051/inspect_layout.py` (main pad 0, aside at y=56).
- Screenshots in `docs/verification/T-051/after/` at 1440 light + dark and 390 light + dark, plus the
  sequence/face-swap tabs; mobile horizontal overflow 0px; the sequence -> face-swap handoff still passes.

## Limits

- Verified locally and then redeployed; the user's own populated rail should be re-checked in the browser.
- The rail still wraps its five kind chips to two rows at 288px. That is intentional (all kinds stay
  one tap away) rather than a scroll.
