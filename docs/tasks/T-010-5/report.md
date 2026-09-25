# Report T-010-5

**Agent:** Buffy@freebuff (z-ai/glm-5.3-flash) · **Role:** implementer (visual) · **Result:** DONE

## Files changed
- `apps/web/src/styles.css` (178 lines): full `@theme` per DESIGN.md §2 — kept the token names (`bg`, `surface`, `border`, `text`, `muted`, `scrim`, `accent`, `accent-ink`) and added `sunken`, `faint`, `success`, `danger`; fonts `--font-display` (Instrument Serif), `--font-body` (Geist), `--font-mono` (JetBrains Mono); `--animate-motion-*` tokens added with the existing keyframes and the `--animate-hf-*` names kept as `var()` aliases; new `status-pulse` (opacity only) and `skeleton-shimmer` (transform only) keyframes; `@layer base` holds `color-scheme: light dark`, body defaults, and the dark `@media (prefers-color-scheme: dark)` token block; serif headings no longer uppercase
- `apps/web/index.html`: title `Reel & Still`; Google Fonts link for Instrument Serif (400 + italic), Geist (400/500/600), JetBrains Mono (400/500) with `display=swap`; Anton/Inter removed; two `<meta name="theme-color">` with `media` for `#F6F3EE` / `#141210`; one-sentence meta description
- `apps/web/public/favicon.svg`: the new mark (accent frame, sprocket notches, record-light dot) — no Higgsfield path data or lime
- `apps/web/src/ui/BrandMark.tsx` (new): original SVG mark in `currentColor` + `BrandWordmark` in `font-display`
- `apps/web/src/ui/AppShell.tsx`: 56px (`h-14`) top bar — brand links `/`, a `Studio` link, right side = new optional `creditsSlot` rendered **before** the existing `rightSlot`; old nav list and the "not affiliated" footer removed; footer is one muted line; new optional `fullBleed` prop removes the main-area padding (default padding kept, so existing routes render as before — **child-controlled padding via `fullBleed`**, noted here per the brief's ask)
- `apps/web/src/ui/buttonStyles.ts`: variants now `primary` (accent fill), `secondary` (surface + 1px border), `ghost` (muted→text); radius 10px, height 40px, `active:scale-[0.98]`, no glow
- `apps/web/src/ui/Button.tsx`, `ButtonLink.tsx`: unchanged code, pick up the new variant map (props/exports untouched)
- `apps/web/src/ui/EmptyState.tsx`: serif headline + 65ch sentence + action, prop-compatible
- `apps/web/src/ui/ProgressBar.tsx`: track is `sunken`; animation alias kept; prop-compatible
- `apps/web/src/ui/Toast.tsx`: DESIGN.md popover surface language (1px border, radius 12px, soft shadow); prop-compatible
- `apps/web/src/ui/GenerationBadge.tsx`: mono micro-label style; **`kind: "sequence"` and the `ffmpeg` → "Stitched" label kept** as the orchestrator's edit requires; prop-compatible
- `apps/web/src/ui/Skeleton.tsx` (new): shimmer block, `motion-safe`, `role="status"`
- `apps/web/src/ui/Tabs.tsx` (new) + `ui/tabKeys.ts` (pure `nextTabIndex`): accessible tablist, arrow/Home/End keys, `aria-selected`, 2px accent underline on the active tab
- `apps/web/src/ui/Popover.tsx` (new) + `ui/popoverKeys.ts` (pure `isDismissKey`): anchored panel, closes on Escape and outside click, returns focus to the trigger; a private `usePopoverDismiss` hook keeps the component ≤ 40 lines
- `apps/web/src/ui/Tabs.test.tsx` (new, 6 tests), `ui/Popover.test.tsx` (new, 2 tests)

## Reused
Existing vitest setup (no new dev deps), `react-dom/server` for component render tests (jsdom is not installed and adding it would be a new dependency), the repo's `ui/` conventions and Tailwind v4 CSS-first token pattern.

## Verify output (brief's command)
```
npm --prefix apps/web run lint      → eslint . (clean, no output)
npm --prefix apps/web run test     → Test Files 11 passed (11) / Tests 68 passed (68)
npm --prefix apps/web run typecheck → tsc -b (clean)
npm --prefix apps/web run build    → ✓ built in 184ms (dist/index.html 1.14 kB, css 40.56 kB, js 364.34 kB)
! grep -riE "higgsfield|anton|ccff00" apps/web/index.html apps/web/src/ui apps/web/src/styles.css
                                   → passes (0 hits)
scripts/check-standards            → ok (0 violations)
```

## Test-environment note
`Tabs.test.tsx` / `Popover.test.tsx` use `react-dom/server` + the extracted pure keyboard helpers because `jsdom`/`@testing-library` are not installed and installing packages is forbidden by the handoff rules. The interactive behaviours (focus movement, outside click, focus return) are covered by the pure helpers (`nextTabIndex`, `isDismissKey`) plus render assertions of `aria-selected`/`tabindex`. T-010-7+ may revisit if a DOM test env lands.

## Evidence
- Screenshots: `docs/verification/T-010-5/home-1440-light.png` (true light render) and `home-1440-dark.png`. Caveat, stated honestly: this headless Chrome (for-testing 151) ignores `--blink-settings=preferredColorScheme`/`--force-dark-mode` for `prefers-color-scheme`, so the dark capture uses `--enable-features=WebContentsForceDark` (Chrome's auto-darkening) rather than a true dark-token render. The dark **token values** are instead verified by the contrast computation below and by reading the CSS: the swap is pure CSS under `@media (prefers-color-scheme: dark)`, so a dark-OS browser gets the dark palette with no JS. The served page was verified to carry `<title>Reel & Still</title>` and the new shell classes (via `--dump-dom`).
- Contrast ratios (WCAG relative luminance, computed from the DESIGN.md §2 values):

| Pair | Light | Dark | AA (4.5) |
|---|---|---|---|
| `text` / `bg` | 15.80 | 15.34 | pass |
| `text` / `surface` | 17.21 | 14.26 | pass |
| `muted` / `surface` | 5.81 | 6.26 | pass |
| `muted` / `bg` | 5.33 | 6.74 | pass |
| `accent-ink` / `accent` (14px/600) | 5.25 | 6.19 | pass |

## Acceptance checks (yes/no + evidence)
- [x] yes — `grep -riE "higgsfield|anton|ccff00" apps/web/index.html apps/web/src/ui apps/web/src/styles.css` returns nothing (verify chain above)
- [x] yes — no hex in any `ui/*.tsx`; colours are only token utilities (`text-accent`, `bg-sunken`, `border-border`, …); the only rgb/rgba literals are shadow/scrim alpha values in existing class strings
- [x] yes — both themes pass AA for body text and the accent pair; ratios table above
- [x] yes — no flash of the light theme: tokens swap in CSS under `@media (prefers-color-scheme: dark)` with `color-scheme: light dark` and per-scheme `<meta name="theme-color">`; no JS theme toggle exists
- [x] yes — all existing pages still compile and render; all 60 pre-existing tests plus the 8 new ones pass
- [x] yes — Tabs and Popover are keyboard-accessible with tests (arrow/Home/End wrap logic unit-tested; `aria-selected`/`tabindex` asserted; Escape dismissal tested via `isDismissKey`)

## Open issues / guesses / things skipped
- The dark screenshot is Chrome's auto-dark approximation, not a true dark-token render (no way to force `prefers-color-scheme` in this headless build without new tooling). The CSS itself was hand-verified against DESIGN.md §2 dark values.
- Feature files (`features/explore/ExplorePage.tsx`, `features/create-video/createVideoCopy.ts`, `features/share/shareCopy.ts`) still set `document.title` containing "Higgsfield" at runtime. Those files are outside Allowed files; the verify grep is scoped to `index.html`, `ui/` and `styles.css` exactly as the brief specifies, and T-010-7/10 rebuild those pages.
- `fullBleed` implemented as an explicit prop (main loses padding when true); the default path is unchanged for existing routes.
- No commit, no new dependencies.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Reel & Still identity: warm-paper/dark tokens in `@theme`, Instrument Serif + Geist + JetBrains Mono, new brand mark + favicon, 56px top bar shell, restyled primitives, new Skeleton/Tabs/Popover (T-010-5) | `apps/web/src/styles.css`, `index.html`, `public/favicon.svg`, `ui/*` | lint/test(68)/typecheck/build green, brand grep 0 hits, check-standards 0 violations, contrast AA both themes, screenshots in `docs/verification/T-010-5/` | 2026-09-25 |
