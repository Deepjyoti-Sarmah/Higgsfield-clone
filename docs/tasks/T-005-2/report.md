# Report T-005-2

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web)
**Result:** DONE

## Files changed
- `apps/web/src/api/guestSession.ts` (new): the spec-004 guest-session runner, moved out of the create-video feature **behaviourally unchanged** (same shared in-flight `ensureGuest` promise, same single 401 retry, same `statusRef`/`startGuestSessionRef` assignment during render). Declares `GuestSessionSource = { status: "loading" | "signed-out" | "signed-in"; startGuestSession: () => Promise<boolean> }` so `api/` imports no feature; `SessionContextValue` is structurally assignable to it, so the create-video call site compiles unchanged. Also owns `GuestSessionOutcome<T>` and `RunWithGuestSession`.
- `apps/web/src/features/create-video/useGuestSessionRunner.ts` (**deleted**): superseded by `api/guestSession.ts`; no forwarding wrapper left behind.
- `apps/web/src/features/create-video/createVideoTypes.ts` (edit, re-export only): removed the two `GuestSessionOutcome`/`RunWithGuestSession` definitions and added `export type { GuestSessionOutcome, RunWithGuestSession } from "../../api/guestSession"` next to the existing `Preset`/`PresetsState` re-export. Every other type in the file is byte-identical.
- `apps/web/src/features/create-video/CreateVideoPage.tsx` (edit, import path only): line 17 `./useGuestSessionRunner` → `../../api/guestSession`. File stays exactly 200 lines.
- `apps/web/src/api/library.ts` (new): `LibraryItem = components["schemas"]["LibraryItemResponse"]`, `LibraryState = { status; items; reloadLibrary }`, `useLibrary(session: GuestSessionSource)`. Fetches through `useGuestSessionRunner(session)` so the 401 → guest → one-retry path is the spec-004 one; `GET /api/v1/jobs` with `params.query.limit = 50`; `outcome !== "done"`, non-200 or throw → `null` → `"error"`; otherwise `data.items` → `"ready"`. Imports **no** `features/**` module.
- `apps/web/src/api/generated/schema.d.ts` (regenerated): `npm --prefix apps/web run gen:api` added the `list_jobs` operation plus `LibraryItemResponse` and `LibraryListResponse`.
- `docs/tasks/T-005-2/report.md` (new): this file.

## Reused
- `apps/web/src/api/presets.ts` (T-006-1 precedent) — `api/library.ts` mirrors its shape 1:1: module-level `fetchX` returning `T[] | null`, `isMountedRef`/`requestIdRef` race guards, `hasItemsRef` no-loading-flash rule, `reloadLibrary` as the Retry callback, `status` union.
- `apps/web/src/api/client.ts` `apiClient` + `api/generated/schema.d.ts` — `LibraryItem` comes from the generated schema; **no hand-written API shape**.
- The moved runner itself, not a reimplementation: `useLibrary` consumes `RunWithGuestSession` from the same module rather than re-deriving 401 handling.
- `createVideoTypes.ts` re-export pattern (`Preset`/`PresetsState`) so `useImageUpload.ts`, `useCreateJob.ts` and `useActiveJob.ts` compile unchanged.

## Verify output (full paste, no summarising)
Command run exactly as given in the brief, from the repo root:

```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

Full output:

```

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


> web@0.0.0 test
> vitest run


 RUN  v5.0.0 /home/deepjyoti/Documents/Assigment/Higgsfield/apps/web

 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests) 16ms
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests) 11ms
 ✓ src/features/create-video/elapsedTime.test.ts (3 tests) 8ms
 ✓ src/features/create-video/imageFileRules.test.ts (4 tests) 10ms
 ✓ src/features/explore/groupPresetsByCategory.test.ts (6 tests) 10ms
 ✓ src/features/explore/recreateHref.test.ts (4 tests) 10ms
 ✓ src/features/create-video/jobStatusWatcher.test.ts (9 tests) 38ms

 Test Files  7 passed (7)
      Tests  53 passed (53)
   Start at  20:14:10
   Duration  365ms (transform 55%, import 24%, tests 14%, worker 7%)


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

✓ built in 402ms
check-standards: ok (0 violations)
```

Exit status of the whole chain: **0** (`VERIFY_EXIT=0`). Passed on the first run; no fixes were needed.

## Standards check
```
check-standards: ok (0 violations)
```
Also clean under the enforced eslint limits: `max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`, naming-convention. New file sizes: `api/guestSession.ts` 52 lines, `api/library.ts` 62 lines. No new comments except the existing "why" note carried over with the runner.

## Two required plain statements

**(a) `npm run typecheck` is a known no-op in this repo; `tsc -b` inside `build` is the real gate.**
`apps/web`'s `typecheck` script is `tsc --noEmit`. The root `tsconfig.json` is a solution-style config (`files: []` with project references), so a bare non-`-b` invocation type-checks no files and exits 0 regardless of type errors. The real type gate is therefore `tsc -b` inside `npm run build`, which *did* run in this verify chain (build step: `tsc -b && vite build`) and passed, compiling 89 modules. Both are present in the pasted output above.

**(b) `gen:api` did change `schema.d.ts`, by 77 insertions and 1 deletion.**
`npm --prefix apps/web run gen:api` was run first, before any hand-written code. `git diff --stat` on the file: **1 file changed, 77 insertions(+), 1 deletion(-)**. The diff is exactly the frozen contract additions:
- `paths["/api/v1/jobs"].get`: `get?: never` → `operations["list_jobs_api_v1_jobs_get"]` (the 1 deletion + 1 insertion).
- `components.schemas.LibraryItemResponse` and `components.schemas.LibraryListResponse` added.
- `operations.list_jobs_api_v1_jobs_get` added (query `limit?: number`; responses 200 `LibraryListResponse`, 401 `ErrorResponse`, 422 `HTTPValidationError`).

No pre-existing path or schema was altered, consistent with spec AC-12. `LibraryItem` in `api/library.ts` is derived from this generated schema.

## Open issues / guesses / things skipped
- **No unit test was added for `useLibrary`.** The brief's acceptance check only requires the existing suite to keep passing, and no component consumes the hook until T-005-4. `api/presets.ts`, the mirrored precedent, likewise has no direct test; its `usePresets` is exercised through components. Hook behaviour is therefore verified by type-check/build plus the mirrored race-guard code, not by execution — flagged honestly rather than claimed as tested.
- **`GuestSessionSource` decoupling is structural, not nominal.** `SessionContextValue` is assignable to it, so `useGuestSessionRunner(session)` in `CreateVideoPage.tsx` compiles with no cast; if that context ever drops `startGuestSession` or changes the status union, the call site fails to compile — which is the intended feedback.
- **`reloadLibrary` stability depends on the runner's `useCallback` identity.** `useGuestSessionRunner` returns a `useCallback` with deps `[ensureGuest]` and `ensureGuest` has `[]`, so the identity is stable across renders and the `useEffect([reloadLibrary])` in `useLibrary` does not re-fire. This is the same invariant `api/presets.ts` relies on; no dependency-array lint warning was emitted.
- **`limit: 50` is hard-coded**, per the brief and design AC-3 ("a single bounded page of 50"); pagination is explicitly out of scope for spec 005.
- **Nothing committed** — left to the orchestrator per the brief. `git status` shows only the six files listed above; `apps/api` was not touched.
- **Contract was already frozen by T-005-0**, so no contract code was changed; `gen:api` consumed the existing `packages/contracts/openapi.json`.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Library web data: shared guest-session runner moved to `api/`, `useLibrary` lists `GET /api/v1/jobs` | `apps/web/src/api/guestSession.ts`, `apps/web/src/api/library.ts` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` (exit 0) | 2026-09-13 14:14 |
