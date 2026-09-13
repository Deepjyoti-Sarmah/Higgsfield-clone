# Report T-006-1

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH), working directly
**Result:** DONE

## Files changed
All paths relative to `apps/web/` unless noted.

| File | New/Edit/Delete | What changed |
|---|---|---|
| `src/api/presets.ts` | New | `Preset`, `PresetCategory`, `PresetsState`, `usePresets` — the hook **moved verbatim** from `features/create-video/usePresets.ts` (same `fetchPresets`, same `loading → ready/error`, same `reloadPresets` retry, same `isMountedRef`/`requestIdRef` guards). Only the import paths changed (`./client`, `./generated/schema`). |
| `src/features/create-video/createVideoTypes.ts` | Edit | Deleted the local `Preset` and `PresetsState` definitions; now `import type { Preset, PresetsState } from "../../api/presets"` + `export type { Preset, PresetsState }`. `PresetCategory = Preset["category"]` and every other type are unchanged, and `components["schemas"][…]` is still the only source of API shapes. |
| `src/features/create-video/usePresets.ts` | Delete | Removed (no forwarding wrapper). |
| `src/features/create-video/CreateVideoPage.tsx` | Edit | One line: `import { usePresets } from "./usePresets"` → `"../../api/presets"`. Nothing else touched. |
| `src/features/explore/exploreCopy.ts` | New | Hero, gallery and state copy + `creditCost`, `recreateAriaLabel`, `previewAlt`, `categoryLabels`, `categoryLabel`. |
| `src/features/explore/toolCards.ts` | New | `ToolCard` type + `TOOL_CARDS` (5 entries, design order). |
| `src/features/explore/groupPresetsByCategory.ts` | New | `PresetGroup` + `groupPresetsByCategory` (fixed order, empty groups omitted, unknown appended first-seen). |
| `src/features/explore/groupPresetsByCategory.test.ts` | New | 6 tests. |
| `src/features/explore/recreateHref.ts` | New | `recreateHref(slug)`. |
| `src/features/explore/recreateHref.test.ts` | New | 4 tests (exact string, encoding, `URLSearchParams` round-trip, unencoded path). |
| `src/features/explore/presetTileStyles.ts` | New | `presetTileStyles` (one literal class string per category) + `DEFAULT_TILE_CLASSES`. |
| `docs/tasks/T-006-1/report.md` | New | This report. |

Nothing outside the brief's Allowed files was touched. **No commit** (the orchestrator owns docs sync + the commit).

### The move, proven
- `usePresets` had exactly one importer and still does: `CreateVideoPage.tsx:21` → `"../../api/presets"`.
- No `"\./usePresets"` import and no `features/create-video/usePresets` reference remains anywhere in `apps/web/src`.
- `PresetPicker.tsx`, `CreateVideoPanel.tsx`, `usePresetSelection.ts` and `CreateVideoPage.tsx` all still import `Preset`/`PresetsState` from `./createVideoTypes`, which now re-exports them — the build proves it compiles.

## Reused
- `api/client.ts` `apiClient` and `api/generated/schema.d.ts` — the moved hook still calls `apiClient.GET("/api/v1/presets")`; `Preset` remains `components["schemas"]["PresetResponse"]`, never hand-written.
- The **existing `usePresets` implementation** — copied, not rewritten; behaviour is byte-for-byte the same logic.
- `features/create-video/usePresetSelection.ts` — **read only, unchanged**; `recreateHref` targets the `?preset=` parameter it already reads.
- Tailwind vocabulary from `PresetCard.tsx` (`bg-gradient-to-br from-border to-bg`, `rounded-xl border-2`), and the `--color-*` tokens in `styles.css`. No new colour, no new dependency, no `styles.css` change.

## Copy fidelity
`docs/specs/006-explore/design.md` § Copy was checked programmatically: the section contains **no non-ASCII inside string literals** (the only non-ASCII characters are the `·` and `→` separators of the tables). The error title uses a plain ASCII apostrophe (`We couldn't load the effects.`), matching the design exactly. All hero, gallery and state strings are copied verbatim.

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


> web@0.0.0 test
> vitest run


 RUN  v5.0.0 /home/deepjyoti/Documents/Assigment/Higgsfield/apps/web

 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests) 7ms
 ✓ src/features/create-video/imageFileRules.test.ts (4 tests) 7ms
 ✓ src/features/create-video/elapsedTime.test.ts (3 tests) 3ms
 ✓ src/features/explore/groupPresetsByCategory.test.ts (6 tests) 9ms
 ✓ src/features/explore/recreateHref.test.ts (4 tests) 5ms
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests) 14ms
 ✓ src/features/create-video/jobStatusWatcher.test.ts (9 tests) 21ms

 Test Files  7 passed (7)
      Tests  53 passed (53)
   Start at  19:26:27
   Duration  235ms (transform 54%, import 26%, tests 13%, worker 7%)


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 78 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-BGBKhcYb.css   25.13 kB │ gzip:   5.37 kB
dist/assets/index-Bg1dAYQJ.js   321.06 kB │ gzip: 100.40 kB

✓ built in 272ms
check-standards: ok (0 violations)
```
Exit status of the chain: **0**. 10 of the 53 tests are the two new files (6 + 4); no test was skipped and no new dependency was added.

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```
`npm run lint` also passed (eslint: `max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`, `naming-convention`). Largest new file: `groupPresetsByCategory.test.ts` at 61 lines.

**Tailwind scanning check** (design § Risks: the fallback classes must be literals): all four class strings are in the built CSS — `from-accent\/30`, `from-accent\/20`, `from-accent\/10` (3 escaped occurrences each) and `from-border`.

## Open issues / guesses / things skipped
1. **Tools copy lives in `toolCards.ts`, not `exploreCopy.ts`.** The brief asks `exploreCopy.ts` to hold "every string in design.md § Copy", but the design's Files table makes `toolCards.ts` the home of the 5 cards (`label`/`description`/`to`) and T-006-2 renders `TOOL_CARDS`. I kept **one** source of truth (the data module) instead of duplicating the ten tool strings in both files. `exploreCopy` holds every other § Copy string. If a reviewer wants the tools mirrored into `exploreCopy`, say so and I will add it — but that would create drift.
2. **`api/presets.ts` also exports `PresetCategory`.** The brief lists `Preset`, `PresetsState`, `usePresets`; the explore helpers need the category type and must not import `features/create-video` internals (STANDARDS feature isolation), so the derived alias lives with the contract type it comes from. `createVideoTypes.ts` keeps its own `PresetCategory = Preset["category"]` alias unchanged, so spec 004's export surface is untouched.
3. **Added `categoryLabel(category)`** (`exploreCopy.gallery.categoryLabel`). The design pins labels for the three known categories, but `groupPresetsByCategory` deliberately appends unknown categories, so a fallback to the raw category string is needed; otherwise T-006-3 has no label for them. T-006-3 should call it instead of indexing `categoryLabels`.
4. **`states.loading.skeletonCount: 6`** carries the design's "6 skeleton tiles" as data next to the `Loading effects` screen-reader string, so T-006-3 does not hardcode either.
5. **Name collision to watch (not mine to fix):** `toolCards.ts` exports the type `ToolCard`, and the design's component tree also names the T-006-2 component `ToolCard`. A file cannot both import that type and declare a `ToolCard` function, so T-006-2 must alias the import (e.g. `import type { ToolCard as ToolCardData }`). I followed the design's type name rather than renaming it unilaterally.
6. **Gradient syntax:** `presetTileStyles.ts` uses `bg-gradient-to-br` (the v4 alias) because that is what `PresetCard.tsx` and `HowItWorksStep.tsx` already use; the newer `bg-linear-to-br` would also work. Verified generated, so the fallback tile is never transparent.
7. **`npm run typecheck` is still a no-op** (root `tsconfig.json` is solution-style; already recorded in `STATUS.md`). The real type gate is the `tsc -b` inside `npm run build`, which passed — including the `createVideoTypes` re-export and the deleted hook.
8. **No contract change, no route added.** `packages/contracts/openapi.json` was not touched and `scripts/export-openapi` was not run (out of scope for a web-only task).
9. **Not run:** the app was not started and no browser check was done (T-006-2/3/4 add the components and routing); `verify-slice` covers that later.
10. **Capture:** my tool cannot be wrapped by `scripts/agent-run`, so per AGENTS.md the orchestrator must export this session's transcript into `.agent-logs/` at commit time.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Explore shared preset data + copy/helpers: `usePresets` moved to `api/presets.ts` and re-exported through `createVideoTypes.ts` (spec 004 unchanged); `exploreCopy`, `TOOL_CARDS`, `groupPresetsByCategory`, `recreateHref`, `presetTileStyles` with 10 new tests | `apps/web/src/api/presets.ts`, `apps/web/src/features/explore/{exploreCopy,toolCards,groupPresetsByCategory,recreateHref,presetTileStyles}.ts` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` → 53 passed (10 new), build ok, 0 violations | 2026-09-13 |
