# Report T-031

**Agent / model / tool:** implementer (UI) · deepseek-flash (DSH main session) · run_code/bash + Playwright-core + chromium
**Result:** DONE

## Files changed
- `apps/web/src/features/explore/ExploreHero.tsx`: compact hero (badge + one headline + one line + two
  CTAs, `py-4`, `text-3xl sm:text-5xl`); the three large showcase cards are gone.
- `apps/web/src/features/explore/ExplorePage.tsx`: stack gap 8 -> 6.
- `apps/web/src/features/explore/ToolCards.tsx` + `ToolCard.tsx`: five boxed dashboard cards -> one thin
  row of text links (`label + tag`), no icons, no boxes.
- `apps/web/src/features/explore/PresetGallery.tsx`: title `text-2xl sm:text-3xl`, dense grid
  `grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-2`, compact category headings, and the
  category section extracted to `PresetGroupSection` to stay inside eslint's 40-line function limit.
  Also added `w-full` (see the flex bug below).
- `apps/web/src/features/explore/PresetGalleryCard.tsx`: media-first tile — the whole tile is one `Link`,
  video/image fills it, name + category overlay the bottom-left scrim, cost chip top-left, and the
  "Recreate" pill appears on hover **and focus-visible**.
- `apps/web/src/ui/AppShell.tsx`: header `py-2`, wordmark `text-base`, footer collapsed to one muted line.
- `apps/web/src/features/create-video/CreateVideoCanvas.tsx`: `min-h-[320px] md:min-h-[420px]`, `p-5`.
- `apps/web/src/styles.css`: new `--color-scrim` token (used by the tile overlay), per STANDARDS.
- `docs/WALKTHROUGH.md`: Beat 1 no longer claims hero showcase cards (removed here).
- `docs/verification/T-031/{before,after}-{explore,create-video}.png`: 1440x900 screenshots.
- `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md`, `.agent-logs/T-031`.

## Reused
- `recreateHref`, `exploreCopy`, `presetTileStyles` (kept alive as the null-preview fallback) and the
  existing `ButtonLink`/`PreviewMedia` patterns. No hooks, `api/`, routes or props changed.

## Tool-cards decision
Compressed to **one thin row of text links** rather than deleted. Rationale: `TOOL_CARDS` data lives in
`features/explore/toolCards.ts`, which T-031's allowed-files list does **not** include; deleting the two
components would leave that module orphaned. The thin row costs ~20px, keeps the data used, and no longer
reads like an admin dashboard. The nav still carries the same five destinations.

## Verify output (full paste, no summarising)
```
npm --prefix apps/web run lint      -> pass (eslint .)
npm --prefix apps/web run test      -> 9 files / 60 tests passed
(cd apps/web && npx tsc -b)         -> tsc -b: ok
npm --prefix apps/web run build     -> built in 359ms (dist/assets/index-*.js 360.69 kB)
scripts/check-standards             -> check-standards: ok (0 violations)

Geometry (Playwright-core + chromium 1234, viewport 1440x900, deviceScaleFactor 1, local build):
{"viewport":1440,"effects":{"x":144,"y":378,"w":1152,"h":647},
 "grid":{"x":144,"y":477,"w":1152,"h":140},
 "gridColumns":"224px 224px 224px 224px 224px",
 "tiles":[{"x":144,"y":477,"w":224,"h":140}, ...],
 "tileCountAboveFold":8}
```
Screenshots at 1440x900: `docs/verification/T-031/before-explore.png` -> `after-explore.png` and
`before-create-video.png` -> `after-create-video.png` (after was captured from the local production build
served by FastAPI on :8041, `GET /api/v1/presets` -> 12/12 non-null).

## Acceptance checks
- [x] Explore shows 8 preset tiles without scrolling past the hero (`tileCountAboveFold: 8`; camera 5 +
      cinematic 3; the dynamic row starts just below 900px).
- [x] A tile has two text rows at rest (name + category); "Recreate" is reachable by keyboard because the
      whole tile is the link and the pill uses `group-focus-visible:inline`.
- [x] No behavior change: guest sign-in, `?preset=` deep link and the create-video flow keep their hooks and
      routes; only markup/classes moved. 60 vitest still pass.
- [x] lint / tsc / test / build / check-standards all pass.
- [x] Before/after screenshots in `docs/verification/T-031/`.

## Open issues / guesses / things skipped
- **Found and fixed a real layout bug:** the gallery was `mx-auto max-w-6xl` inside a flex column. Auto
  cross-axis margins disable flex stretch, so the section shrink-wrapped to content (measured 425px wide,
  77px tiles) instead of filling. `w-full` restores the 1152px container (verified by re-measuring).
  The same pattern may affect Library/Credits (out of scope here).
- **The preview media is our ffmpeg-synthesised gradient footage** (T-030). It is honest and ours, but the
  wall reads as coloured panels rather than photos; swapping in licensed photos later is a media change with
  no code path impact.
- The dynamic category's 4 tiles sit just below the 900px fold; the brief asked for 8 tiles, not 12.
- The create-image/Library/Credits/Share pages were not touched (out of scope).

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Explore density pass: full-width 5-up media-first gallery (whole tile is the link, name/category overlay, Recreate on hover+focus), compact hero, tool cards reduced to one text row, slimmer shell | `apps/web/src/features/explore/*`, `apps/web/src/ui/AppShell.tsx`, `apps/web/src/styles.css` | Playwright at 1440x900 -> `tileCountAboveFold: 8`, grid 1152px / 224px tiles; lint + tsc + 60 vitest + build + `scripts/check-standards` ok; screenshots in `docs/verification/T-031/` | 2026-09-14 04:35 |
