# Tasks 006: Explore (signed-out landing page)

Rules:
- One task = one agent run.
- No two tasks share a file; the Files lists below are the disjoint split of design.md's **Files** table
  (checked in T-006-0).
- Every task has a verify command. The full, copy-pasteable command is in each brief.
- Paths are repo-relative; `apps/web/`-relative paths from design.md carry the prefix here.
- Task ownership comes straight from design.md's **AC → design → task map** and **Files** table; no other file may
  be touched.

**Waves:** T-006-1 → (T-006-2 ∥ T-006-3) → T-006-4.
T-006-2 and T-006-3 are independent of each other (hero/tools vs gallery) but both read T-006-1's copy, tool-card
data and pure helpers. T-006-4 is gated on both because `ExplorePage` renders every section.

- [x] **T-006-0** · Design spec 006 (spec, design, this file, the four briefs, report)
  - Files: `docs/specs/006-explore/**`, `docs/tasks/T-006-*/**`
  - Verify: `python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))" && ls docs/tasks | grep T-006 && scripts/check-standards`
  - Suggested role: designer (strongest model) · Depends on: —
- [x] **T-006-1** · Shared preset data hook, Explore types/copy/data and the pure helpers (+ unit tests)
  - Files:
    - `apps/web/src/api/presets.ts`
    - `apps/web/src/features/create-video/createVideoTypes.ts` (re-export only)
    - `apps/web/src/features/create-video/usePresets.ts` (delete)
    - `apps/web/src/features/create-video/CreateVideoPage.tsx` (import path only)
    - `apps/web/src/features/explore/{exploreCopy,toolCards,groupPresetsByCategory,groupPresetsByCategory.test,recreateHref,recreateHref.test,presetTileStyles}.ts`
    - `docs/tasks/T-006-1/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-006-0
- [x] **T-006-2** · Hero and tool cards
  - Files:
    - `apps/web/src/features/explore/{ExploreHero,ToolCard,ToolCards}.tsx`
    - `docs/tasks/T-006-2/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-006-1
- [x] **T-006-3** · Effect gallery: cards, per-category sections and the three states
  - Files:
    - `apps/web/src/features/explore/{PresetGallery,PresetGalleryCard,PresetGalleryStates}.tsx`
    - `docs/tasks/T-006-3/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-006-1
- [x] **T-006-4** · Assemble `ExplorePage`, route `/` to it and retire `HomePage`
  - Files:
    - `apps/web/src/features/explore/ExplorePage.tsx`
    - `apps/web/src/App.tsx`
    - `apps/web/src/features/home/HomePage.tsx` (delete)
    - `docs/tasks/T-006-4/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-006-2, T-006-3
