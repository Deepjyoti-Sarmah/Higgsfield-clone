# Brief T-006-4: Assemble `ExplorePage`, route `/` to it and retire `HomePage`

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/006-explore/spec.md` (AC-1, AC-2, AC-3, AC-7, AC-8)
- Design: `docs/specs/006-explore/design.md` sections **Route + layout**, **Component tree**, **Props**, **Shared preset data**, **Files**
- Provided by T-006-1/2/3: `apps/web/src/api/presets.ts` (`usePresets`), `apps/web/src/features/explore/{ExploreHero,ToolCards,PresetGallery}.tsx`
- Existing patterns: `apps/web/src/App.tsx`, `apps/web/src/features/home/HomePage.tsx` (the file you retire), `apps/web/src/features/create-video/CreateVideoPage.tsx` (read for the page-assembly style; do not edit it)
- `apps/web/src/features/create-video/usePresetSelection.ts` — **read only**: it is what consumes the `?preset=` parameter your Recreate links set.

## Goal
Assemble the three Explore sections into one page, make it the index route `/`, and delete the superseded home page — so a signed-out visitor landing on `/` sees hero + tool cards + the 12 effects.

## Allowed files (touch nothing else)
- `apps/web/src/features/explore/ExplorePage.tsx` (new)
- `apps/web/src/App.tsx` (edit)
- `apps/web/src/features/home/HomePage.tsx` (delete)
- `docs/tasks/T-006-4/report.md`

## Must reuse
- `usePresets` from `apps/web/src/api/presets.ts` — call it **once** in `ExplorePage` and pass the resulting `PresetsState` to `PresetGallery`. Do not fetch presets again inside a child.
- `ExploreHero`, `ToolCards`, `PresetGallery` unchanged; if one needs a prop that does not exist, report it instead of editing it here.
- `ui/AppShell` stays the layout (it already renders the 5-item nav, including "Explore" → `/`). Do not change it.
- Do not read the session in `ExplorePage`: the page must render identically signed out.

## Acceptance checks
- [ ] `ExplorePage` renders, in order: `ExploreHero`, `ToolCards`, `PresetGallery` (with the `PresetsState` from the single `usePresets()` call).
- [ ] `App.tsx`'s index route (`index`) renders `ExplorePage`; the `HomePage` import is gone; no other route or the `AppShell` wiring changes.
- [ ] `apps/web/src/features/home/HomePage.tsx` is deleted. `grep -rn "features/home\|HomePage" apps/web/src` returns nothing.
- [ ] No session/login gate: with no cookie (signed out) the page renders hero + tools + gallery; browsing and Recreate need no session.
- [ ] `npm run build` type-checks and builds (this is the real type gate; `npm run typecheck` is a known no-op in this repo).
- [ ] Manual check recorded in the report (may be SKIPPED, say so): with the API up (`docker compose up -d --wait db && uv --directory apps/api run uvicorn app.main:app --port 8000`) and `npm --prefix apps/web run dev`, open `/` signed out → 12 preset cards in 3 groups, names visible without hover, and clicking Recreate lands on `/create/video?preset=<slug>` with that preset selected.
- [ ] No file over 200 lines; no function over 40 lines; complexity ≤ 8 (`npm run lint`).

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any component T-006-2/T-006-3 owns, `usePresets`/`api/presets.ts`, `ui/AppShell`, `styles.css`, `package.json`.
- The P1 sample-outputs gallery and per-preset previews (spec 006 § Out of scope).
- Contract/API changes.

## Report
Write `docs/tasks/T-006-4/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
