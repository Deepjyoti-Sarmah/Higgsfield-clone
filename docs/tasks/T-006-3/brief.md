# Brief T-006-3: Effect gallery — cards, per-category sections and the three states

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/006-explore/spec.md` (AC-1, AC-4, AC-5, AC-6, AC-8, AC-9)
- Design: `docs/specs/006-explore/design.md` sections **Component tree**, **Props**, **Recreate deep-link**, **Copy § Gallery**, **Copy § States**, **Accessibility**, **Test strategy**, **Files**
- Contract: `packages/contracts/openapi.json`, `PresetResponse` (`slug`, `name`, `description`, `category`, `credit_cost`, `preview_url: string | null`)
- Provided by T-006-1: `apps/web/src/features/explore/{exploreCopy,groupPresetsByCategory,recreateHref,presetTileStyles}.ts`, `apps/web/src/api/presets.ts` (`Preset`, `PresetsState`)
- Existing patterns: `apps/web/src/ui/EmptyState.tsx`, `apps/web/src/ui/Button.tsx`, `apps/web/src/ui/ButtonLink.tsx`, `apps/web/src/features/create-video/PresetCard.tsx` (read for the visual language; do not edit or import it)

## Goal
The effect gallery: one card per preset with the name always visible and a "Recreate" link, grouped into camera → cinematic → dynamic sections, plus the loading, error and empty states. It must render identically signed out.

## Allowed files (touch nothing else)
- `apps/web/src/features/explore/PresetGallery.tsx` (new)
- `apps/web/src/features/explore/PresetGalleryCard.tsx` (new)
- `apps/web/src/features/explore/PresetGalleryStates.tsx` (new)
- `docs/tasks/T-006-3/report.md`

## Must reuse
- `groupPresetsByCategory` (T-006-1) for the grouping and category order — do not re-implement grouping in the component.
- `recreateHref` (T-006-1) for the Recreate target — never build the query string inline.
- `presetTileStyles` (T-006-1) for the fallback tile classes; use `DEFAULT_TILE_CLASSES` when `category` is unexpected.
- `exploreCopy.gallery` / `exploreCopy.states` (T-006-1) for every string, including `creditCost(credits)`, `recreateAriaLabel(name)` and `previewAlt(name)`.
- `ui/EmptyState` for the error and empty states, and `ui/Button` for "Retry". Do not add a new state primitive.
- Router `Link` (react-router-dom) for "Recreate" so keyboard, middle-click and open-in-new-tab all work.

## Acceptance checks
- [ ] `PresetGallery` renders the section with `id="effects"` (the hero's secondary CTA target), the gallery title/subtitle, and one `<section aria-labelledby>` per non-empty category in the fixed order camera → cinematic → dynamic.
- [ ] Each category heading has a stable `id` and the section counts in `aria-labelledby`; the list is a `<ul>` with one `<li>` per preset.
- [ ] `PresetGalleryCard` shows the preset **name as a text node**, its category label, `creditCost(preset.credit_cost)` ("20 credits"), and a "Recreate" `Link` to `recreateHref(preset.slug)` whose accessible name is `recreateAriaLabel(preset.name)`.
- [ ] `preview_url` present → render an `<img>` with `alt={previewAlt(preset.name)}` and `loading="lazy"`; `preview_url` null → render the decorative fallback tile with `aria-hidden="true"` and no image request.
- [ ] `PresetGalleryStates` renders: loading → `aria-busy="true"` region with skeleton tiles (no layout shift when the gallery replaces it); error → `EmptyState` with the error copy and a "Retry" `Button` calling `onRetry`; empty → `EmptyState` with the empty copy and **no** Retry.
- [ ] `PresetGallery` picks the state from `PresetsState.status` and from `presets.length === 0` while ready, and otherwise renders the grouped gallery.
- [ ] Nothing is hover-only: every name, category and cost is readable without pointer interaction.
- [ ] No file over 200 lines; no function over 40 lines; complexity ≤ 8; `max-depth` ≤ 3 (`npm run lint`).

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Hero and tool cards (T-006-2), `ExplorePage`/routing (T-006-4).
- Per-preset video previews (spec 006 § Out of scope): render `preview_url` only.
- Editing T-006-1's files. If a helper or string is missing, report it instead of adding it here.
- Contract/API changes, `styles.css`, `package.json`, any create-video file.

## Report
Write `docs/tasks/T-006-3/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
