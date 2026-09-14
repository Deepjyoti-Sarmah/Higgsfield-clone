# Brief T-036: Match the reference Explore gallery (masonry, no chrome, hover reveal)

**Role:** implementer (small/medium model is fine — this brief is prescriptive) · **Visual only, no logic changes**

## Look at these two images before you start
- **Target:** `docs/research/screenshots/03-explore-visual-effects.png`
- **Ours now:** `docs/verification/explore.png`

## The seven differences to close
| # | Reference | Ours now |
|---|---|---|
| 1 | ONE continuous masonry wall of tiles | Split into "CAMERA 5" / "CINEMATIC 3" / "DYNAMIC 4" section rows |
| 2 | Tiles are **different heights** (some ~2× taller), portrait-biased | Every tile the same 4:3 box |
| 3 | Tiles are bare video — no border, no card background, ~8px radius | Bordered rounded-2xl card with `p-4` padding |
| 4 | **Nothing** written on a tile at rest | "20 credits" chip always visible, plus name + category text under every tile |
| 5 | On hover: dark scrim + big uppercase name + "✦ Recreate" pill, centred | Recreate button always visible below the tile |
| 6 | Section header: acid-green heavy uppercase title, grey subtitle, and a yellow pill CTA right-aligned on the same line | Title + subtitle only, no CTA, CTA lives in the hero |
| 7 | Grid runs nearly edge to edge (~16px side margins) | Centred container with wide empty gutters |

## Exact spec

**Section header** (one row, `flex items-start justify-between`):
- Left: `EFFECTS` in the display font, uppercase, `text-4xl`, accent colour; subtitle under it in `text-muted text-sm`.
- Right: a `Try for free` pill button linking to `/create/video` — reuse `ui/ButtonLink` with the primary (accent) variant.

**Grid** — CSS columns is the simplest true masonry and it keeps the DOM flat:
```
<div className="columns-2 gap-3 px-4 sm:columns-3 lg:columns-4 xl:columns-5 [column-fill:_balance]">
  {presets.map(p => <div key={p.slug} className="mb-3 break-inside-avoid"><PresetGalleryCard .../></div>)}
</div>
```
- Drop the per-category section wrappers. Render all 12 presets in one list, ordered by `sort_order`.
- Keep `groupPresetsByCategory.ts` and its test in the repo (Create video still uses category chips) — just stop calling it from the Explore gallery.

**Varying tile heights.** Our 12 previews are all 16:9, so uniform tiles would look nothing like the reference. Give each tile one of three aspect ratios by index, and let `object-cover` crop:
```
const TILE_ASPECTS = ["aspect-[3/4]", "aspect-[9/16]", "aspect-[4/5]"]
// index % 3, so the wall has short / tall / medium tiles like the reference
```

**Tile** (`PresetGalleryCard.tsx`):
- Outer: `group relative block overflow-hidden rounded-lg` — **remove** the border, the `bg-surface`, the `p-4`, and the `hover:-translate-y-1`.
- Video: keep the existing `poster` + `preload="metadata"` + `object-cover h-full w-full`. Keep `motion-reduce:` variants.
- **Delete from the resting state:** the credits chip, the name, the category line, and the always-visible Recreate button.
- **Hover/focus overlay** — one absolutely-positioned layer, `opacity-0` → `opacity-100` on `group-hover:` and `group-focus-within:`, `transition-opacity duration-200`:
  - scrim `absolute inset-0 bg-black/55`
  - name: display font, uppercase, `text-xl text-white text-center`, centred
  - under it a `✦ Recreate` pill, accent background, dark text
  - `{preset.credit_cost} credits` in `text-xs text-white/70` beneath
- The whole tile stays one `<Link to={recreateHref(preset.slug)}>` so it's keyboard-reachable, and `group-focus-within` makes the overlay appear on focus, not just hover.

**Touch devices must not lose the names.** Add a block so the overlay is permanently visible where hover does not exist:
```
@media (hover: none) { .preset-overlay { opacity: 1 } }
```
Put that in `apps/web/src/styles.css` under `@layer base`, and give the overlay that class alongside the Tailwind utilities.

## Allowed files
- `apps/web/src/features/explore/{PresetGallery,PresetGalleryCard,ExplorePage,exploreCopy,presetTileStyles}.tsx|ts`
- `apps/web/src/styles.css`

## Do not touch
- Anything under `create-video/`, `image-create/`, `library/`, `session/`
- `apps/web/src/api/`, any hook, any `.test.ts`
- `apps/web/src/api/imageJobs.ts` and `imageJobHelpers.ts` — another agent's in-flight work, never stage or commit these

## Acceptance checks
- [ ] Explore shows one continuous masonry of 12 tiles with visibly different heights
- [ ] At rest a tile shows **only video** — no text, no chip, no button
- [ ] Hover **and** keyboard focus both reveal the name + Recreate overlay
- [ ] Clicking any tile still lands on `/create/video?preset=<slug>`
- [ ] Tiles still show a poster still-frame before the clip buffers (do not remove `poster`)
- [ ] Section header has the right-aligned CTA
- [ ] No horizontal scroll at 390px width; grid is 2 columns there

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```
Then screenshot Explore at 1440×900 and at 390×844, save to `docs/verification/T-036/after-explore-desktop.png` and `after-explore-mobile.png`, and compare against `docs/research/screenshots/03-explore-visual-effects.png`.

## Out of scope
The hero, the tool-card row, the header, the footer, and every other page. Explore's gallery only.

## Report
`docs/tasks/T-036/report.md`: what you changed, the verify output, and an honest note on which of the seven differences you did **not** close. Do NOT commit — the orchestrator reviews the screenshots first.
