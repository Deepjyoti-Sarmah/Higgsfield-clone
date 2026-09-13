# Report T-006-3

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH), working directly
**Result:** DONE

## Files changed
| File | New/Edit | Responsibility |
|---|---|---|
| `apps/web/src/features/explore/PresetGallery.tsx` | New | `id="effects"` section + title/subtitle; picks loading / error / empty / grouped; one `<section aria-labelledby>` per non-empty category; `<ul>` with one `<li>` per preset |
| `apps/web/src/features/explore/PresetGalleryCard.tsx` | New | one effect card: preview or decorative fallback tile, name, category, cost, "Recreate" link |
| `apps/web/src/features/explore/PresetGalleryStates.tsx` | New | loading skeleton region, error `EmptyState` + Retry, empty `EmptyState` |
| `docs/tasks/T-006-3/report.md` | New | this report |

Nothing else was touched. **No commit** (the orchestrator owns docs sync + the commit).

## How the acceptance points are met
- **`id="effects"`** is on the outer `<section>`, so T-006-2's hero secondary CTA (`#effects`) has a real, stable target. The outer section is named via `aria-labelledby="effects-title"`.
- **Category sections:** one `<section aria-labelledby={effects-<category>}>` per **non-empty** group, in the fixed order the grouping helper returns (camera → cinematic → dynamic, unknown appended). Each `<h2>` carries that stable id, so the section's accessible name is the heading; the preset count sits inside the heading in a muted span.
- **Lists:** the `<ul>` grid holds one `<li>` per preset; the card itself is an `<article>`, so the card stays list-agnostic while the gallery owns list semantics.
- **Card content:** name is a real `<h3>` text node, the category label and `creditCost(preset.credit_cost)` ("20 credits") are plain `<p>` text — nothing is hover-only.
- **Recreate:** a react-router `<Link>` with `to={recreateHref(preset.slug)}` and `aria-label={recreateAriaLabel(preset.name)}`, so keyboard, middle-click and open-in-new-tab all work and the twelve links do not all announce as "Recreate".
- **Preview:** `preview_url !== null` → `<img src alt={previewAlt(name)} loading="lazy">`; `preview_url === null` → a decorative `<span aria-hidden="true">` with `presetTileStyles[category] ?? DEFAULT_TILE_CLASSES` and **no `<img>` element at all**, so no image request is made.
- **State selection:** `status === "loading" | "error"` from `PresetsState`, and empty when `status === "ready" && presets.length === 0`; otherwise the grouped gallery.
- **Loading region:** `aria-busy="true"` with the `Loading effects` screen-reader string, three category headings from `exploreCopy.gallery.categoryLabels`, and **2 skeleton tiles each = the design's 6 tiles**. Skeleton tiles reuse the gallery's grid and `aspect-[4/3]` box so the swap is close to shift-free.
- **Error / empty:** `ui/EmptyState` with the design's exact copy; the error variant gets a `ui/Button` "Retry" calling `onRetry`, the empty variant gets **no** action. No new state primitive was added.

`grep` confirms the only string literals in the three files are status values (`"loading"`, `"ready"`, `"error"`, `"empty"`) — every user-visible string comes from `exploreCopy`.

## Reused
- `groupPresetsByCategory` (T-006-1) for grouping and order — no grouping logic in the component.
- `recreateHref` (T-006-1) for every Recreate target — the query string is never built inline.
- `presetTileStyles` + `DEFAULT_TILE_CLASSES` (T-006-1) for the fallback tile.
- `exploreCopy.gallery` / `exploreCopy.states` + `categoryLabel` / `creditCost` / `recreateAriaLabel` / `previewAlt` (T-006-1) for every string.
- `ui/EmptyState`, `ui/Button`, react-router `Link`; `styles.css` tokens only (`bg-surface`, `border-border`, `text-muted`, `text-text`, `accent/60`, `bg-border`); the `focus-visible:outline-accent` pattern from `ui/buttonStyles.ts`.

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 78 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-BjvPsqQJ.css   26.22 kB │ gzip:   5.59 kB
dist/assets/index-PeQHeFU-.js   321.06 kB │ gzip: 100.40 kB

✓ built in 349ms
check-standards: ok (0 violations)
```
Exit status of the chain: **0**.

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```
`npm run lint` also passed (`max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`, `naming-convention`). File sizes: `PresetGallery.tsx` 54, `PresetGalleryCard.tsx` 52, `PresetGalleryStates.tsx` 71 lines.

## Open issues / guesses / things skipped
1. **Heading levels follow design.md literally:** § Accessibility says "One `h1` (hero); each category is an `h2`". So category headings are `<h2>` and the gallery title ("Effects") is a `<p id="effects-title">` used as the outer section's `aria-labelledby`, **not** a heading — otherwise "Effects" would be a second competing `h2`. If a reviewer wants the gallery title to be a real heading, that is a heading-level decision across T-006-2/3/4 (hero `h1` → gallery `h2` → category `h3`); flagged rather than decided unilaterally.
2. **Skeleton exact-height parity is not achievable.** spec.md says the loading state shows "three category headings with skeleton tiles"; design § Copy § States says "6 skeleton tiles". I satisfied both: 3 headings × 2 tiles = 6, derived from `skeletonCount` / the number of category labels (no hardcoded 6 or 2). The real gallery renders 12 presets (4 per category → 2 rows each), so the skeleton is shorter than the loaded page; "no layout shift" is approximated by reusing the same grid and `aspect-[4/3]` box, not guaranteed. Say the word if you would rather have 6 tiles under a single heading, or 4 per category.
3. **`preview_url` is `null` for all 12 presets today**, so only the decorative tile branch renders in practice. The `<img>` branch is implemented and type-checked but is not exercised by real data; it makes no request while `preview_url` is null.
4. **Alt text repeats the name** (`"<name> preview"` on the image, `<name>` in the `<h3>`) — that is the design's specified alt string, kept verbatim.
5. **Unknown category labels** go through `exploreCopy.gallery.categoryLabel`, so an unexpected category still renders its raw name as the heading instead of an empty one.
6. **One tab stop per card** by construction: only the Recreate `<Link>` is interactive; the name/category/cost are text. (This is the deliberate opposite of the T-002-7 button-inside-link bug.)
7. **Not verified in a browser.** Explore is not routed until T-006-4 wires `ExplorePage`, so the visual result (grid breakpoints, card heights, skeleton spacing) is reasoned from the classes; `verify-slice` is the intended check. No unit tests were added — the brief lists none for this task and the repo's vitest is Node-only with no jsdom.
8. **`npm run typecheck` remains a no-op** (root `tsconfig.json` is solution-style); the real gate is `tsc -b` inside `npm run build`, which passed. `tsconfig.app.json` has `include: ["src"]`, so these unreferenced files are type-checked even though they are not yet in the JS bundle (78 modules, unchanged).
9. **Capture:** my tool cannot be wrapped by `scripts/agent-run`, so per AGENTS.md the orchestrator must export this session's transcript into `.agent-logs/` at commit time.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Explore effect gallery: `id="effects"` section, per-category `aria-labelledby` sections in camera → cinematic → dynamic order, cards with always-visible name/category/cost and an accessible "Recreate" deep link, plus loading skeleton / error+Retry / empty states | `apps/web/src/features/explore/{PresetGallery,PresetGalleryCard,PresetGalleryStates}.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → all pass, 0 violations | 2026-09-13 |
