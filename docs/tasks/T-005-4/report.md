# Report T-005-4

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`, see Open issues
**Result:** DONE

## Files changed
- `apps/web/src/features/library/useLibraryJobParam.ts` (new): reads `?job=<id>` via `useSearchParams`, writes it with `{ replace: true }` on select, and derives `selectedItem` / `isMissing` from the loaded list.
- `apps/web/src/features/library/LibraryPage.tsx` (new): takes `useOutletContext<SessionContextValue>()`, calls `useLibrary(session)` once, maps `loading|error|empty|list` and renders title/subtitle → `LibraryStates` → `LibraryList` → `LibraryResultView`.
- `apps/web/src/features/library/LibraryList.tsx` (new): `<ul>` with one `<li>` per item, forwards `selectedJobId` + `onSelect`.
- `apps/web/src/features/library/LibraryItem.tsx` (new): one `<button>` per row: `alt=""` thumbnail (or `aria-hidden` decorative tile), preset name, `formatCreatedAt`, text status, `aria-current` and `openLabel(preset_name)`.
- `apps/web/src/features/library/LibraryStates.tsx` (new): loading (`aria-busy="true"` + `srText` + `skeletonCount` rows mirroring the item layout), error (`EmptyState` + `Button` Retry), empty (`EmptyState` + caller-supplied action).
- `apps/web/src/features/library/LibraryResultView.tsx` (new): succeeded → `<video controls muted autoPlay loop playsInline>` + Download link + "Make another" deep link; failed → `error_message ?? failedFallback`, never a video; missing → `item.missing`.
- `docs/tasks/T-005-4/report.md` (new): this report.

## Reused
- `apps/web/src/api/library.ts` — `LibraryItem`, `LibraryState`, `useLibrary` (T-005-2), called exactly once in `LibraryPage`.
- `apps/web/src/features/library/libraryCopy.ts` + `formatCreatedAt.ts` (T-005-3) — every user-visible string and the time text.
- `apps/web/src/features/session/useSession.ts` — `SessionContextValue` outlet context (the HomePage/CreateVideoPage precedent).
- `apps/web/src/ui/EmptyState.tsx`, `ui/Button.tsx`, `ui/ButtonLink.tsx`, `ui/buttonStyles.ts` — no new primitives.
- `react-router-dom` `useSearchParams` (the `?job=` param) and `useOutletContext`.
- The `PresetGallery` / `PresetGalleryStates` list + skeleton layout as the visual pattern (not imported — feature isolation).

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
✓ 89 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-GXi1qc62.css   26.75 kB │ gzip:   5.67 kB
dist/assets/index-kkZN2yhM.js   327.55 kB │ gzip: 102.12 kB

✓ built in 478ms
check-standards: ok (0 violations)
```

Extra (not part of the brief's verify command, run for confidence):
```
$ npm --prefix apps/web run test
 ✓ src/features/explore/groupPresetsByCategory.test.ts (6 tests)
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests)
 ✓ src/features/explore/recreateHref.test.ts (4 tests)
 ✓ src/features/create-video/elapsedTime.test.ts (3 tests)
 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests)
 ✓ src/features/create-video/imageFileRules.test.ts (4 tests)
 ✓ src/features/create-video/jobStatusWatcher.test.ts (9 tests)
 ✓ src/features/library/formatCreatedAt.test.ts (4 tests)
 Test Files  8 passed (8)
      Tests  57 passed (57)
```

## Standards check
```
scripts/check-standards: ok (0 violations)
```
Per-file lines: `LibraryPage.tsx` 48 · `LibraryList.tsx` 24 · `LibraryItem.tsx` 41 · `LibraryStates.tsx` 55 · `LibraryResultView.tsx` 74 · `useLibraryJobParam.ts` 32 — every file is far under 200. ESLint enforces `max-lines-per-function: 40`, `max-depth: 3` and `complexity: 8` and passed; the most complex functions are `LibraryResultView` and `deriveStatesStatus` at complexity 4. No user-visible string literal in any component — `grep` of the six files shows text only through `libraryCopy` (the only bare literals are `type="button"`, class names, `alt=""`, `aria-*` tokens and `loading="lazy"`). No `/jobs/{id}` call exists in the feature (`grep -rn "jobs/" apps/web/src/features/library/` → none), so AC-5's "no second API call" holds by construction.

## Open issues / guesses / things skipped
- **`LibraryResultView` prop widened to `LibraryItemData | null`.** The design § Props table says `{ item: LibraryItemResponse }` and the brief says to follow it "exactly", but the same brief bullet also assigns the AC-7 missing panel to `LibraryResultView` ("a selected id that is not in the list → `item.missing`"). Rendering `null` as `item.missing` is the only way to satisfy both without adding a second prop/component or a string literal in the page. Everything else in the Props table matches verbatim.
- **`useLibraryJobParam(items)` takes the list.** The design Files table only names "`?job=` read/write + missing detection"; the brief says the hook reports whether the selected id is absent from the list, so it needs the items to compare against. The page additionally requires `state.status === "ready"` before trusting `isMissing`, otherwise a refresh with `?job=<id>` would flash "no longer available" during the first load.
- **Queued/running items are selectable** (one button per row is AC-11) and the result panel shows their text status with no video. The brief only specifies succeeded / failed / missing; this is the least-surprising non-video panel and uses `libraryCopy.item.status`.
- **`libraryCopy.result.close` is unused.** The design Props table gives `LibraryResultView` only `item` (no close handler) and the brief lists no Close action, so a Close button could not be wired without adding a prop outside the design.
- **"Make another" href is inlined** (`/create/video?preset=${encodeURIComponent(preset_slug)}`) instead of importing explore's `recreateHref`: STANDARDS forbids one feature importing another's internals and the shared location (`ui/` or `api/`) is outside this task's allowed files. Candidates for a follow-up move on the rule of two.
- **Not reachable yet.** `/library` is still `App.tsx`'s placeholder (T-005-5 owns the route), so `LibraryPage` is compiled and linted but not in the production bundle (89 modules, unchanged). It was not rendered in a browser — this CLI session has no browser; the visual/AC pass belongs to `verify-slice` once T-005-5 lands.
- **No `.agent-logs/` entry.** This run went through the DSH harness, not `scripts/agent-run`, and the brief scopes this task to the six files + this report; the orchestrator owns capture/commit.
- No commit made (orchestrator does); no T-005-2/T-005-3 file, `ui/**`, `styles.css`, `package.json` or other feature was touched (`git status --short` lists exactly the six new files + this report).

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Library page UI: `?job=` selection (replace-state), `<ul>`/`<li>` list with one real row button per item (thumbnail/decorative tile, preset name, UTC time, text status, `aria-current`, `openLabel`), `aria-busy` skeleton / error+Retry / empty states, and a result panel that renders the video + Download + "Make another" from the list item with no `/jobs/{id}` call (failed/missing panels included) | `apps/web/src/features/library/{LibraryPage,LibraryList,LibraryItem,LibraryStates,LibraryResultView}.tsx`, `apps/web/src/features/library/useLibraryJobParam.ts` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → build ok (89 modules), 0 violations; `npm --prefix apps/web run test` → 57 passed (browser AC pass deferred to `verify-slice`, route lands in T-005-5) | 2026-09-13 20:34 |
