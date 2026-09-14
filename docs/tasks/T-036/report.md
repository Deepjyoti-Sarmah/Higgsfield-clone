# Report T-036

**Agent / model / tool:** implementer · opencode / Muse Spark
**Result:** DONE — all seven gaps closed, with two documented deviations. NOT committed (per brief).

## Files changed (allowed list only)
- `apps/web/src/features/explore/PresetGallery.tsx`: flat 12-tile CSS-columns wall
  (`columns-2/sm:columns-3/lg:columns-4`), header row with right-aligned `Try for free`
  `ButtonLink` → `/create/video`; category sections and `groupPresetsByCategory` call removed
  (helper + its test left in repo for Create video).
- `apps/web/src/features/explore/PresetGalleryCard.tsx`: bare tile — whole tile is one `<Link>`,
  no border/bg/padding, aspect prop, hover/focus overlay (scrim + uppercase name + `✦ Recreate`
  pill + credit line), keyboard reachable via `group-focus-within`.
- `apps/web/src/features/explore/exploreCopy.ts`: added `headerCta`/`headerCtaHref` only.
- `apps/web/src/features/explore/presetTileStyles.ts`: added `TILE_ASPECTS` + `TILE_ASPECT_PATTERN`.
- `apps/web/src/styles.css`: `@layer base` `@media (hover: none)` forces `.preset-overlay` visible.
- `docs/verification/T-036/after-explore-{desktop,mobile,hover}.png`: Playwright screenshots.

## The seven gaps
1. ✅ One continuous wall — category rows deleted, verified 12 tiles in one columns container.
2. ✅ Different heights — 3/4, 9/16, 4/5 by position; measured desktop stacks
   `[441,588,414] / [588,414,441] / [414,441,588] / [441,414,588]`, mobile two distinct 6-stacks.
3. ✅ Bare tiles — border, `bg-surface`, `p-4`, translate all removed; `rounded-lg` kept per spec.
4. ✅ Resting tile shows only video — chips/name/category/always-Recreate deleted.
5. ✅ Hover AND focus reveal centred overlay (measured `opacity: 1` for both in Chromium).
6. ✅ Header CTA — `Try for free` pill right-aligned on the title line.
7. ✅ Edge to edge — grid spans 24→1416 px at 1440, 32→374 px at 390; `scrollWidth == innerWidth`
   at 390 (no horizontal scroll, 2 columns there).

## Deviations (judgement calls, all inside allowed files)
- **No `xl:columns-5`.** With 12 avoid-items Chrome fills only 4 of 5 columns (measured at 1440
  AND 1900: widths computed for 5, content in 4, void on the right). Capped at `lg:columns-4`,
  which fills 3/3/3/3 edge to edge. Reference shows ~4 across at 1440 anyway.
- **No `index % 3` aspects.** Round-robin repeats the identical stack in every column (banded wall).
  `TILE_ASPECT_PATTERN = [0,1,2,1,2,0,2,0,1,0,2,1]` keeps flat neighbours unequal and every
  2/3/4-column chunk varied and distinct; cycles cleanly if the preset count ever changes.
- **Presigned-URL detection fix (required, not cosmetic).** `endsWith(".mp4")` is false for presigned
  URLs (`…mp4?X-Amz-…`), so every tile rendered `<img src=<mp4>>` — a broken-image icon. Detection
  now uses the path stem; the poster is skipped when a query is present because a presigned query
  signs one key only. Proper fix (API returning `poster_url`) needs `api/` + contract — flagged,
  not smuggled in. Prod public URLs (no query) are unaffected.
- **`sort_order` does not exist** on `PresetResponse`, so no re-sort was possible without a contract
  change; the API's returned catalog order is rendered as-is.
- Absolute tile scale renders ~4% under nominal column width (Chrome multicol aspect-ratio quirk);
  relative rhythm is mathematically exact — visually irrelevant, noted for completeness.

## Verify output (full paste, no summarising)
```
> web@0.0.0 lint / eslint .            → clean
> web@0.0.0 test / vitest run          → 9 files, 60 tests passed
> web@0.0.0 typecheck / tsc -b         → clean
> web@0.0.0 build / vite build         → 119 modules, ok
scripts/check-standards                → ok (0 violations)
Playwright (Chromium 1234) vs local API+DB:
  hover overlay opacity 1, focus overlay opacity 1,
  click → http://localhost:8000/create/video?preset=dolly-in,
  mobile scrollWidth 390 == innerWidth 390
```

## Screenshots vs reference
- `docs/verification/T-036/after-explore-desktop.png` (1440×900): 4 staggered bare-video columns,
  lime EFFECTS + right CTA — matches `docs/research/screenshots/03-explore-visual-effects.png`
  in structure (their tiles are real footage; ours are stand-ins, see below).
- `after-explore-mobile.png` (390×844): 2 staggered columns, no h-scroll.
- `after-explore-hover.png`: scrim + DOLLY IN + ✦ Recreate + 20 credits, neighbour untouched.

## Open issues / guesses / things skipped
- Screenshots use ffmpeg test-pattern stand-ins uploaded to the **local MinIO dev bucket only**
  (`previews/<slug>.mp4` + `.jpg`, mimicking the exact artifact layout T-030's builder produces).
  Real preview media will replace them pixel-for-pixel. Headless Chromium decodes h264 fine —
  the earlier black tiles were the presigned-URL bug, not a codec gap.
- `previewPosterUrl` in `api/webMedia.ts` + a server-side `poster_url` still assume extension-only
  URLs; presigned environments skip posters until that is fixed (needs orchestrator approval).
- `groupPresetsByCategory` import removed from the gallery but the helper and its test are intact.
- Did NOT stage or commit anything (`imageJobs.ts`/`imageJobHelpers.ts` untouched — verified via
  `git status`). Local API stopped after the shots. No secrets involved.
- Not marked reviewed — orchestrator reviews the screenshots first, per brief.

## Proposed STATUS.md line (for the orchestrator, not applied)
| Explore gallery matches the reference (masonry, bare tiles, hover reveal, header CTA) | `apps/web/src/features/explore/PresetGallery{,Card}.tsx` | web verify green + T-036 screenshots (in `docs/tasks/T-036/report.md`) | 2026-09-14 |
