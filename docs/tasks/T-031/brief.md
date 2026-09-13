# Brief T-031: Density pass — make the UI look like the reference, not a dashboard

**Role:** implementer with UI sense (strong model) · **Runs after T-030** (needs real preview media to judge the result)

## Problem
Compare our pages with the research screenshots:
- `docs/research/screenshots/03-explore-visual-effects.png` — a dense, edge-to-edge masonry wall of moving video. Names appear **on** the tile on hover. Almost no chrome.
- `docs/research/screenshots/16-video-create-empty.png` — a compact control column, and a canvas dominated by preview media.

Ours: a sparse 3-up grid of boxed cards with big padding, a title, a category line, a credit line and a lime pill button under each — five stacked text rows per tile. Plus a row of five "tool cards" that reads like an admin dashboard. The layout skeleton is right; the **density and hierarchy** are wrong.

## Goal
Content-forward pages where the media is the interface. Visual only — no behaviour, no API, no hook changes.

## Allowed files
- `apps/web/src/features/explore/{ExplorePage,ExploreHero,PresetGallery,PresetGalleryCard,PresetGalleryStates,ToolCard,ToolCards,presetTileStyles,exploreCopy}.tsx|ts`
- `apps/web/src/features/create-video/{CreateVideoPage,CreateVideoPanel,CreateVideoCanvas,PresetPicker,PresetCard,PresetCategoryChips,HowItWorks,HowItWorksStep,CanvasHeading}.tsx`
- `apps/web/src/ui/{AppShell,Button,buttonStyles,EmptyState}.tsx|ts`
- `apps/web/src/styles.css`

## The changes
**Gallery cards (biggest win)**
- Media fills the tile. Move the name **onto** the tile as a bottom-left overlay over a gradient scrim; keep it visible at rest (our "better than the original" rule — reference hides it until hover, which fails on touch).
- Category and credit cost become one small muted line or a corner chip, not two stacked rows.
- "Recreate" appears on hover/focus as an overlay button on the tile; the whole tile is the link. Keep it keyboard-reachable.
- Result: two text rows per tile, not five.

**Grid density**
- Explore gallery: 2 cols at mobile → 3 at `md` → 4 at `lg` → 5 at `xl`, gap ~12px. Today's 3-up with wide gaps and `p-4` cards wastes half the viewport.
- Drop the per-card outer padding and border; let tiles sit flush with a small radius.

**Hero**
- Tighten the vertical space (the current hero eats a full viewport before any content). Headline + one line + the two buttons, then the gallery starts above the fold on a 900px-tall window.

**Tool cards**
- Five dashboard cards duplicating the nav is the weakest block on the page. Either delete them (the nav already covers it) or compress into one thin row of text links. Your call — justify it in the report.

**Chrome**
- `AppShell`: slimmer header, smaller wordmark, less vertical padding.
- Footer: one line, muted.

**Create video**
- Preset picker tiles get the same media-first treatment at small size.
- The "three steps" canvas panel should not be taller than the control column on a 900px window.

**Tokens** — put any new spacing/radius/scrim values in the `@theme` block in `styles.css` per `docs/STANDARDS.md` (Tailwind v4, no `tailwind.config.js`, no CSS modules, no hardcoded hex in components).

## Constraints
- **No logic changes.** Do not touch hooks, `api/`, routing, or anything under `features/*/use*.ts`. If a component's props must change, keep the call sites in your allowed list.
- No new dependencies. No animation library.
- Every file stays ≤200 lines.
- Keep existing `aria-label`s, focus states and `motion-reduce:` variants. Hover-only affordances must have a focus-visible equivalent.

## Acceptance checks
- [ ] On a 1440×900 window, Explore shows **at least 8 preset tiles** without scrolling past the hero
- [ ] A gallery tile has at most two text rows at rest; "Recreate" is reachable by keyboard
- [ ] Nothing regressed: guest sign-in, `?preset=` deep link from a tile, and the create-video flow still work
- [ ] `npm run lint`, `tsc -b`, `npm run test`, `npm run build`, `scripts/check-standards` all pass
- [ ] Before/after screenshots of Explore and Create video in `docs/verification/T-031/`

## Verify command (paste full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npx --prefix apps/web tsc -b && npm --prefix apps/web run build && scripts/check-standards
```
Then, with the local stack running, click through: Explore → Recreate on a tile → image upload → Generate. Screenshot both pages.

## Out of scope
- Preview media (T-030 owns it), the Modal backend, copy rewrites beyond removing rows you delete, Library/Credits/Share pages.

## Report
`docs/tasks/T-031/report.md` from `docs/templates/report.md`, including the tool-cards decision and the before/after screenshots. Commit with a plain message, no attribution trailers, including `.agent-logs/`.
