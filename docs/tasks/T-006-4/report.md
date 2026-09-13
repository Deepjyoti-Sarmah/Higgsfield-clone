# Report T-006-4

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH), working directly
**Result:** DONE

## Files changed
| File | New/Edit/Delete | What changed |
|---|---|---|
| `apps/web/src/features/explore/ExplorePage.tsx` | New | Calls `usePresets()` **once**, sets the page title, renders `ExploreHero` → `ToolCards` → `PresetGallery` (27 lines) |
| `apps/web/src/App.tsx` | Edit | Exactly 2 lines: the import (`HomePage` → `ExplorePage`) and the index route element |
| `apps/web/src/features/home/HomePage.tsx` | Delete | Retired; `features/home/` was empty afterwards and was removed |
| `docs/tasks/T-006-4/report.md` | New | This report |

Nothing else was touched: `AppShell`, `useSession`/`GuestButton`/`SessionBadge` wiring, the other five routes, and every T-006-1/2/3 file are unmodified. **No commit** (the orchestrator owns docs sync + the commit).

`git diff apps/web/src/App.tsx` is exactly:
```
-import { HomePage } from "./features/home/HomePage"
+import { ExplorePage } from "./features/explore/ExplorePage"
-        <Route index element={<HomePage />} />
+        <Route index element={<ExplorePage />} />
```

## Requested confirmations
- **No remaining `HomePage` import.** `grep -rn "features/home\|HomePage" apps/web/src` → **no matches** (the only three hits before this task were `App.tsx:5`, `App.tsx:33` and the file's own declaration).
- **`tsc -b` inside `build` passes with the new index route.** `npm run build` is `tsc -b && vite build`; it exited 0. The module count rose 78 → **89** and the bundle 321.06 kB → **327.55 kB**, which is the index route now pulling in `ExplorePage` + hero + tool cards + gallery.
- **No session gate.** `grep -rn "useSession\|useOutletContext\|GuestButton\|SessionBadge" apps/web/src/features/explore/` → no matches, so the page cannot read a session; it renders identically signed in or out. `AppShell` still supplies the header/`rightSlot`, unchanged.

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
dist/assets/index-BAq81MA2.css   26.26 kB │ gzip:   5.60 kB
dist/assets/index-JSzd9XX0.js   327.55 kB │ gzip: 102.12 kB

✓ built in 200ms
check-standards: ok (0 violations)
```
Exit status of the chain: **0**.

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```
`npm run lint` also passed (`max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`). `ExplorePage.tsx` is 27 lines and its only function body is the hook call + JSX.

## Manual check — browser step SKIPPED, real evidence substituted
**The click-through is SKIPPED: this CLI session has no browser** (no chromium/chrome, no playwright/puppeteer/cypress — the same limitation recorded for T-004-5). So I did **not** observe rendered cards or click "Recreate".

Instead I ran the stack for real (`docker compose up -d --wait db`, `alembic upgrade head`, `uvicorn app.main:app --port 8000` with the built SPA, `GENERATION_BACKEND=mock`) and captured this, signed out with **no cookie**:

```
=== GET /api/v1/presets (signed out, no cookie) ===
HTTP 200
presets: 12
per category: {'camera': 5, 'cinematic': 3, 'dynamic': 4}
all credit_cost 20: True
all preview_url null: True
=== SPA at / ===
HTTP 200  bytes=748
<script type="module" crossorigin src="/assets/index-JSzd9XX0.js">
=== deep link /create/video?preset=dolly-in (SPA history fallback) ===
HTTP 200
```
Then, against the exact bundle the server served (`index-JSzd9XX0.js`, 327 558 bytes):
```
  ✓ present: Make your next video
  ✓ present: Browse effects
  ✓ present: Every effect is a camera move
  ✓ present: No effects yet.
  ✓ present: We couldn't load the effects.
  ✓ present: Loading effects
  ✓ present: Turn a photo into a 5-second clip.
  ✓ present: Recreate
  ✓ present: Explore · Higgsfield
=== old home-page-only copy must be gone ===
  ✓ old HomePage copy gone
```
So: the data the gallery needs is live (12 presets, 3 categories, all 20 credits, all `preview_url` null → every card renders its decorative fallback tile), the server serves the built SPA at `/`, the `?preset=` deep-link target is routable, and the served bundle contains every Explore string **and no HomePage copy**. What remains unverified is purely the visual/click layer, which `verify-slice` covers.

## Reused
- `usePresets` from `api/presets.ts` — called **once**; the resulting `PresetsState` is passed straight to `PresetGallery`. No child fetches presets.
- `ExploreHero`, `ToolCards`, `PresetGallery` imported unchanged; no prop needed adding.
- `ui/AppShell` unchanged as the layout, including the 5-item nav whose "Explore" already points at `/`.
- The `usePageTitle` pattern from `CreateVideoPage.tsx` (set on mount, restore on unmount) for `document.title`.

## Open issues / guesses / things skipped
1. **Two `document.title` literals live in `ExplorePage.tsx`** — `"Explore · Higgsfield"` (the brief's exact string) and the `"Higgsfield"` restore, mirroring `CreateVideoPage`'s `usePageTitle`. `exploreCopy` has no title string (spec 004 keeps its own in `createVideoCopy.page`), and `exploreCopy.ts` is T-006-1's file, so I did not add one. If the title should be copy-driven, that is a one-line addition to `exploreCopy` plus this page — flagged rather than done out of scope. I restore the title on unmount (the brief only said "while mounted"); without it, `/` would leave the Explore title on every later route.
2. **Real category counts are 5 / 3 / 4, not 4 / 4 / 4.** This confirms the loading-skeleton caveat T-006-3 recorded: its skeleton is 2 tiles per category (6 total, per the design), so the swap is shorter than the loaded gallery (12 cards) and "no layout shift" remains an approximation. Now measured, not guessed.
3. **`features/home/` no longer exists on disk** — `HomePage.tsx` was the only file, so I removed the empty directory too. Git tracks no directory, so this is invisible in the diff.
4. **`npm run typecheck` is still a no-op** (root `tsconfig.json` is solution-style; already in `STATUS.md`); the real gate is `tsc -b` inside `build`, which passed. `tsconfig.app.json` includes all of `src`, so `ExplorePage` and the deleted `HomePage` were both genuinely type-checked.
5. **No browser check and no unit tests.** The brief lists no test file for this task and the repo's vitest is Node-only (no jsdom), so page assembly is covered by the substituted evidence above plus `verify-slice`.
6. **Capture:** my tool cannot be wrapped by `scripts/agent-run`, so per AGENTS.md the orchestrator must export this session's transcript into `.agent-logs/` at commit time. `.agent-logs/` was outside my allowed files, so I did not create it.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Explore assembled as the index route: `/` renders hero → 5 tool cards → the grouped effect gallery from one `usePresets()` call; `HomePage` retired (no references remain) | `apps/web/src/features/explore/ExplorePage.tsx`, `apps/web/src/App.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → 89 modules built, 0 violations; signed-out `GET /api/v1/presets` → 200 with 12 presets; served bundle contains the Explore copy and no HomePage copy (full output in `docs/tasks/T-006-4/report.md`) | 2026-09-13 |
