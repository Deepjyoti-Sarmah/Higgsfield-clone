# Report T-006-0

**Agent / model / tool:** orchestrator / designer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `docs/specs/006-explore/spec.md` (new): problem, user story, AC-1…AC-10, the four UI states, out of scope (incl. the P1 sample-outputs gallery), open questions.
- `docs/specs/006-explore/design.md` (new): AC → design → task map, the one API contract used (no change), route/layout, component tree + exact props, the shared-preset-data decision, the Recreate deep-link contract, the full copy table, accessibility, test strategy, the 20-file Files table and risks.
- `docs/specs/006-explore/tasks.md` (new): waves T-006-1 → (T-006-2 ∥ T-006-3) → T-006-4, disjoint file sets and a verify command per task.
- `docs/tasks/T-006-{1..4}/brief.md` (new): one delegation brief per task, from `docs/templates/delegation-brief.md`.
- `docs/tasks/T-006-0/report.md` (this file).
- `docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md` (board sync), `.agent-logs/` (session capture).

## Reused
- `docs/playbooks/spec-new.md` (the process), `docs/templates/{spec,design,tasks,delegation-brief}.md` (the shapes).
- `docs/research/product-map.md` rows 10/11/12 and `docs/research/flows/explore.md` (evidence; D-012 locks the scope).
- `docs/specs/004-create-video/design.md` conventions: AC map, Files table, parallel-safe task split, the `?preset=` deep-link contract and its `usePresetSelection` reader.
- `packages/contracts/openapi.json`: `GET /api/v1/presets` → `PresetListResponse` with `PresetResponse` (`credit_cost`, nullable `preview_url`). No new route.
- Existing web pieces: `ui/{AppShell,Button,ButtonLink,EmptyState}`, `api/client.ts`, `features/create-video/usePresets.ts` (moved), `styles.css` tokens, `eslint.config.js` limits.

## Verify output (full paste, no summarising)
```
$ python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))"
/api/health
/api/v1/auth/guest
/api/v1/credits
/api/v1/jobs
/api/v1/jobs/{job_id}
/api/v1/jobs/{job_id}/events
/api/v1/me
/api/v1/presets
/api/v1/uploads
/api/v1/uploads/{asset_id}/complete
-> exit 0

$ ls docs/tasks | grep T-006
T-006-0
T-006-1
T-006-2
T-006-3
T-006-4
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

=== verify command: all steps exit 0 ===
```

## Extra evidence (beyond the required command)

```
=== extra evidence 1: contract is byte-identical (no route/schema change) ===
$ (cd apps/api && uv run --quiet python -c "import json;from app.main import create_app;print(json.dumps(create_app().openapi(),indent=2))") > /tmp/openapi.fresh
$ diff -q /tmp/openapi.fresh packages/contracts/openapi.json
(no difference)
$ sha256sum packages/contracts/openapi.json
17addc27c46ed4662c609e3c95fa58f7f8d973b1bc3804daabf3e02fac6fc9a9  packages/contracts/openapi.json

=== extra evidence 2: no two T-006 tasks share a file (design Files table) ===
Files-table rows: 20  unique files: 20  claimed by >1 task: 0
  T-006-1: 11 files
  T-006-2: 3 files
  T-006-3: 3 files
  T-006-4: 3 files

=== extra evidence 3: every spec AC appears in the AC -> design -> task map ===
spec ACs: 10  mapped: 10  missing: []

=== extra evidence 4: every path referenced by the pack exists or is planned as New ===
  OK                       New    src/api/presets.ts
  OK                       Edit   src/features/create-video/createVideoTypes.ts
  OK                       Delete src/features/create-video/usePresets.ts
  OK                       Edit   src/features/create-video/CreateVideoPage.tsx
  OK                       New    src/features/explore/exploreCopy.ts
  OK                       New    src/features/explore/toolCards.ts
  OK                       New    src/features/explore/groupPresetsByCategory.ts
  OK                       New    src/features/explore/groupPresetsByCategory.test.ts
  OK                       New    src/features/explore/recreateHref.ts
  OK                       New    src/features/explore/recreateHref.test.ts
  OK                       New    src/features/explore/presetTileStyles.ts
  OK                       New    src/features/explore/ExploreHero.tsx
  OK                       New    src/features/explore/ToolCard.tsx
  OK                       New    src/features/explore/ToolCards.tsx
  OK                       New    src/features/explore/PresetGalleryCard.tsx
  OK                       New    src/features/explore/PresetGallery.tsx
  OK                       New    src/features/explore/PresetGalleryStates.tsx
  OK                       New    src/features/explore/ExplorePage.tsx
  OK                       Edit   src/App.tsx
  OK                       Delete src/features/home/HomePage.tsx
  OK                       New    docs/tasks/T-006-{1..4}/report.md
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **No contract change, by design.** P0 Explore is a read of the existing public `GET /api/v1/presets`; the design proves `openapi.json` is byte-identical (`sha256 17addc27…`). Nothing was added because nothing was needed — the instruction allowed a new route only if genuinely required.
- **The P1 sample-outputs gallery is deliberately out of scope** (spec § Out of scope). It needs real sample assets and possibly a public list route; that would be a new contract and its own spec. Row 12 stays unimplemented, not silently dropped.
- **`preview_url` is `null` for all 12 presets**, so gallery cards render a static tile. The card renders the image when the field is populated, so no card change is needed later.
- **`npm run typecheck` is a no-op** in this repo (solution-style tsconfig; already a `STATUS.md` BROKEN row). Every T-006 verify command therefore includes `npm run build`, whose `tsc -b` is the real type gate.
- **T-006-1 edits spec 004's files.** Moving `usePresets` to `api/presets.ts` touches `createVideoTypes.ts` (re-export only) and `CreateVideoPage.tsx` (one import path) and deletes `features/create-video/usePresets.ts`. This was measured: `usePresets` has exactly one importer, and the re-export keeps every other `./createVideoTypes` import compiling. It is one task's file set, so the no-overlap rule still holds.
- **Component behaviour is not unit-tested.** Vitest runs in a Node environment here (no jsdom), matching spec 004's T-004-2 note, so only the pure helpers get tests. Loading/error/focus behaviour is covered by `verify-slice` on the live URL once Explore ships.
- **`verify-slice` was not run** for this task: it is a design pack, and there is no live URL yet (deploy is a user placeholder, `docs/runbooks/deploy.md`).
- **Spec status is APPROVED** on the same convention spec 004 used: handing the pack off (this task) is the human approval, and the scope itself is already locked by D-012.
- **Explore replaces `HomePage` at `/`.** The nav's first item already points at `/` and is labelled "Explore", so no nav change is needed; the old hero copy is a strict subset of the new hero.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Spec 006 (Explore) design pack: signed-out landing page — hero, 5 tool cards, 12-preset gallery with Recreate deep-linking into `/create/video?preset=`; no contract change; 4 parallel-safe briefs with 0 shared files | `docs/specs/006-explore/{spec,design,tasks}.md`, `docs/tasks/T-006-{1..4}/brief.md` | `python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))" && ls docs/tasks \| grep T-006 && scripts/check-standards` -> 10 paths unchanged, T-006-0..4 present, 0 violations; contract `sha256 17addc27…`, 10/10 ACs mapped, 20 files claimed by exactly one task (full output in `docs/tasks/T-006-0/report.md`) | 2026-09-13 03:45 |
