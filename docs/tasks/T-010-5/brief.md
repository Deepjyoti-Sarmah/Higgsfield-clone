# Brief T-010-5: Design tokens, fonts, brand mark, top bar and UI primitives

**Role:** implementer (visual) · **Suggested model:** medium · **Depends on:** nothing · **Wave:** W1

## Start here (any harness)
1. `scripts/task claim T-010-5 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md` § Styling (Tailwind v4, CSS-first, tokens only in `@theme`, **no** `tailwind.config.js`).
3. Read **`DESIGN.md` at the repo root, completely.** It's the spec for this task. Then read the `design-taste-frontend` skill (`.agents/skills/design-taste-frontend/SKILL.md`) for implementation discipline. Where the two disagree, DESIGN.md wins.
4. Read every file under `apps/web/src/ui/` and `apps/web/src/styles.css` before changing them.
5. Questions: `scripts/task say T-010-5 QUESTION "…"`.

## Goal
The app wears the Reel & Still identity: warm-paper light theme, a dark theme from `prefers-color-scheme`, Instrument Serif, Geist and JetBrains Mono, the new brand mark, and a new top bar. Every existing screen still renders and every test passes. The existing pages will look half-new until later tasks rebuild them, and that's expected.

## Allowed files (touch nothing else)
- `apps/web/index.html`
- `apps/web/public/favicon.svg`
- `apps/web/src/styles.css`
- `apps/web/src/ui/*`, existing and new files. New: `BrandMark.tsx`, `Skeleton.tsx`, `Tabs.tsx`, `Popover.tsx`.
- `docs/tasks/T-010-5/report.md`, `docs/verification/T-010-5/*.png`

## The change
1. **`styles.css` `@theme`:**
   - Replace the palette with the DESIGN.md §2 light values. **Keep the existing token names** (`bg`, `surface`, `border`, `text`, `muted`, `scrim`, `accent`, `accent-ink`) so the untouched feature files still compile, and add `sunken`, `faint`, `success` and `danger`.
   - Fonts: `--font-display: "Instrument Serif", …serif`, `--font-body: "Geist", system-ui, sans-serif` and `--font-mono: "JetBrains Mono", ui-monospace, monospace`.
   - Add `--animate-motion-*` tokens (same keyframes) next to the existing `--animate-hf-*` ones. **Keep the `hf` names as aliases for now**; T-010-8 moves their last user and removes them.
   - Add a status-pulse animation (opacity only) and a skeleton shimmer (transform only).
2. **Dark theme:** in `@layer base`, `@media (prefers-color-scheme: dark) { :root { --color-…: … } }` with the DESIGN.md dark values. Put `color-scheme: light dark` on `:root`, and body defaults (`bg-bg text-text font-body`, antialiased).
3. **`index.html`:**
   - Title `Reel & Still`.
   - Google Fonts link for Instrument Serif (400, 400 italic), Geist (400/500/600) and JetBrains Mono (400/500) with `display=swap`. Remove Anton and Inter.
   - Two `<meta name="theme-color">` tags with `media` for light (`#F6F3EE`) and dark (`#141210`).
   - A meta description of one plain sentence.
4. **Brand:**
   - `ui/BrandMark.tsx`: an original SVG mark using `currentColor`. A small frame (a rounded rectangle with two sprocket notches) with a filled dot inside, read as a still and a record light. No Higgsfield path data.
   - Wordmark: "Reel & Still" in `font-display`.
   - `public/favicon.svg`: the same mark in the accent colour.
5. **`ui/AppShell.tsx`:**
   - A 56px top bar: brand (links to `/`), a "Studio" link (`/studio`), and then on the right the existing `rightSlot` plus a new optional `creditsSlot` prop rendered before it.
   - Remove the old nav list and the footer's "not affiliated with Higgsfield" line. The footer becomes one muted line: "Reel & Still · a small studio for short films".
   - The main area gets no forced padding when a route asks for full-bleed. Add a `fullBleed` prop, or let the child control its own padding, and note which in the report.
6. **Primitives:** restyle `Button`, `ButtonLink`, `buttonStyles` (variants `primary`, `secondary`, `ghost`), `EmptyState` (serif headline + sentence + action), `ProgressBar`, `Toast` and `GenerationBadge` to DESIGN.md §4, **keeping their props and exports compatible** so feature code compiles unchanged. Add:
   - `Skeleton` (a shimmer block, `motion-safe`);
   - `Tabs` (an accessible tablist: arrow-key navigation, `aria-selected`, underline active state);
   - `Popover` (anchored, closes on Escape and on an outside click, returns focus to the trigger).
7. **Tests:** add `ui/Tabs.test.tsx` (arrow keys move the selection; `aria-selected` is correct) and `ui/Popover.test.tsx` (Escape closes and focus returns), using the repo's vitest setup.

## Acceptance checks
- [ ] `grep -ri "higgsfield\|anton\|ccff00" apps/web/index.html apps/web/src/ui apps/web/src/styles.css` returns nothing
- [ ] No hex value in any `ui/*.tsx` file; all colours come from tokens
- [ ] Both themes: body text contrast is AA. Put the checked pairs and their ratios in the report
- [ ] No flash of the light theme when the OS is dark (tokens swap in CSS; no JS theme toggle)
- [ ] Existing pages still render; all existing tests pass
- [ ] Tabs and Popover are keyboard-accessible, with tests

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && ! grep -riE "higgsfield|anton|ccff00" apps/web/index.html apps/web/src/ui apps/web/src/styles.css
```
Also: run `npm --prefix apps/web run dev`, then screenshot `/` at 1440px in light and dark into `docs/verification/T-010-5/`. The screenshots are evidence only; the verify command above is the gate.

## Out of scope
- Page layouts, routes, features (T-010-7 onwards). A theme toggle button (the OS setting only).

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-5`
2. `scripts/task submit T-010-5 --as <you> [--transcript <file>]`
