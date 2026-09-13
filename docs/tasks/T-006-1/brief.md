# Brief T-006-1: Shared preset data, Explore copy/data and pure helpers

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/006-explore/spec.md` (AC-3, AC-4, AC-5, AC-6, AC-7)
- Design: `docs/specs/006-explore/design.md` sections **Shared preset data**, **Recreate deep-link**, **Copy**, **Test strategy**, **Files**
- Contract: `packages/contracts/openapi.json`, path `GET /api/v1/presets` → `PresetListResponse { presets: PresetResponse[] }`
- Existing patterns: `apps/web/src/features/create-video/usePresets.ts` (the hook you are moving), `apps/web/src/features/create-video/createVideoTypes.ts`, `apps/web/src/api/client.ts`, `apps/web/src/features/create-video/usePresetSelection.ts` (**read it, do not change it** — it is the `?preset=` consumer your link targets)
- Enforced limits: `apps/web/eslint.config.js` (`max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`)

## Goal
One shared `usePresets` in `apps/web/src/api/presets.ts` used by both features, plus Explore's copy table, the five tool cards as data, and the pure helpers (`groupPresetsByCategory`, `recreateHref`, `presetTileStyles`) with vitest tests. After this task T-006-2, T-006-3 and T-006-4 import from your files and never edit them.

## Allowed files (touch nothing else)
- `apps/web/src/api/presets.ts` (new)
- `apps/web/src/features/create-video/createVideoTypes.ts` (edit: re-export only)
- `apps/web/src/features/create-video/usePresets.ts` (delete)
- `apps/web/src/features/create-video/CreateVideoPage.tsx` (edit: the `usePresets` import path only)
- `apps/web/src/features/explore/exploreCopy.ts` (new)
- `apps/web/src/features/explore/toolCards.ts` (new)
- `apps/web/src/features/explore/groupPresetsByCategory.ts` (new)
- `apps/web/src/features/explore/groupPresetsByCategory.test.ts` (new)
- `apps/web/src/features/explore/recreateHref.ts` (new)
- `apps/web/src/features/explore/recreateHref.test.ts` (new)
- `apps/web/src/features/explore/presetTileStyles.ts` (new)
- `docs/tasks/T-006-1/report.md`

## Must reuse
- `apps/web/src/api/generated/schema.d.ts`: `Preset = components["schemas"]["PresetResponse"]`. Never re-declare an API shape by hand.
- `apps/web/src/api/client.ts` `apiClient`: the moved hook keeps using `apiClient.GET("/api/v1/presets")`.
- The **existing implementation** of `usePresets` (loading → ready/error, `reloadPresets`, the mounted/request-id refs). Move it, do not rewrite its behaviour. Behaviour change is out of scope.
- design.md § Copy is normative: the tool-card labels/descriptions/routes, the hero strings, the gallery strings and the three state strings must match exactly.
- Tailwind class scanning: the fallback-tile classes are **literal** strings only — no template-built class names.

## Acceptance checks
- [ ] `api/presets.ts` exports `Preset`, `PresetsState` and `usePresets`; behaviour is identical to the old hook (same status transitions, same `reloadPresets` retry, same unmount/race guards).
- [ ] `createVideoTypes.ts` no longer **defines** `Preset`/`PresetsState` but re-exports them from `../../api/presets`, so every existing `from "./createVideoTypes"` import still compiles. All other types in that file are unchanged and `components["schemas"][…]` remains the only source.
- [ ] `features/create-video/usePresets.ts` is deleted and `CreateVideoPage.tsx` imports `usePresets` from `../../api/presets`. No forwarding wrapper file is left behind.
- [ ] `exploreCopy.ts` holds every string in design.md § Copy, including `recreateAriaLabel(name)`, `previewAlt(name)` and `creditCost(credits)`.
- [ ] `toolCards.ts` exports `TOOL_CARDS` with exactly 5 entries in the design's order: Explore `/`, Create video `/create/video`, Create image `/create/image`, Library `/library`, Credits `/credits`.
- [ ] `groupPresetsByCategory(presets)` returns groups in the fixed order camera → cinematic → dynamic, omits empty groups, keeps every input preset exactly once, and appends any unknown category in first-seen order rather than dropping it.
- [ ] `recreateHref(slug)` returns exactly `/create/video?preset=<encodeURIComponent(slug)>`; the test round-trips it through `new URLSearchParams(href.split("?")[1])`.
- [ ] `presetTileStyles.ts` maps each `PresetCategory` to a literal Tailwind class string plus a `DEFAULT_TILE_CLASSES` fallback.
- [ ] `npm --prefix apps/web run test` passes with the two new test files; no new dependency is added.

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any `.tsx` component (T-006-2/3/4), `App.tsx`, `features/home/**`, `styles.css`, `package.json`.
- Changing `usePresetSelection.ts` or any other create-video file beyond the four listed.
- Contract/API changes: this spec adds no route and changes no schema. If you believe one is needed, stop and say so in the report.

## Report
Write `docs/tasks/T-006-1/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
