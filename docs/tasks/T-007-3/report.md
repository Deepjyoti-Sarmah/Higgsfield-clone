# Report T-007-3

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `apps/web/src/api/share.ts` (new, 69 lines): `PublicJob = components["schemas"]["PublicJobResponse"]`, `PublicJobState = { status: "loading" | "ready" | "notFound" | "error"; job: PublicJob | null; reload: () => void }` and `usePublicJob(jobId)`. A module-level `fetchPublicJob` returns a three-way `PublicJobOutcome` (`ready` / `notFound` / `error`): 404 → `notFound`, 200 + data → `ready`, any other status, missing data, or a throw → `error`. `jobId === undefined` short-circuits to `notFound` with no request. The hook mirrors `api/presets.ts`: `isMountedRef` + `requestIdRef` race guards, `hasJobRef` so a reload after data does not flash the skeleton, and `reload` as the Retry/Refresh callback. Imports only `react`, `./client`, `./generated/schema` — no `features/**`, no `guestSession`, no credits.
- `apps/web/src/features/share/shareCopy.ts` (new, 40 lines): the `documentTitle(name)` template plus one exported `shareCopy` object (`page` / `states.loading|error|notFound|notReady|failed` / `result.download`), every string byte-exact from design.md § Copy. Pure ASCII.
- `apps/web/src/api/generated/schema.d.ts` (**regenerated**, +83/−0): see below — required because the type the brief names was missing.
- `docs/tasks/T-007-3/report.md`: this report.

## `gen:api` was required (the brief's "if missing" branch)
`PublicJobResponse` and the `GET /api/v1/public/jobs/{job_id}` path were **missing** from `apps/web/src/api/generated/schema.d.ts`, even though `packages/contracts/openapi.json` already contained them (T-007-0 published the contract but did not regenerate the web client). So, exactly as the brief instructs, I ran `npm --prefix apps/web run gen:api` **before writing any code**:

```
$ npm --prefix apps/web run gen:api
> openapi-typescript ../../packages/contracts/openapi.json -o src/api/generated/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../../packages/contracts/openapi.json → src/api/generated/schema.d.ts [77.7ms]
$ git diff --numstat apps/web/src/api/generated/schema.d.ts
83      0       apps/web/src/api/generated/schema.d.ts
```
The diff is **+83 / −0 — purely additive** (`git diff … | grep -E '^-[^-]'` prints nothing): the new path, the `read_public_job_api_v1_public_jobs__job_id__get` operation and `components.schemas.PublicJobResponse` (`id`, `status`, `preset_slug`, `preset_name`, `poster_url`, `video_url`, `created_at`). No pre-existing path or schema changed, so spec AC-11 (contract discipline) holds. This file is outside the brief's three "allowed files", but the brief explicitly authorises this command when the type is missing; flagged here per the hard rule. Note this regeneration is also what unblocks T-007-4/T-007-5.

## Reused
- `apps/web/src/api/presets.ts` — the shared-hook shape mirrored 1:1 (module-level `fetchX`, `isMountedRef`/`requestIdRef` race guards, `hasRef` no-loading-flash rule, `reload` callback, status union).
- `apps/web/src/api/client.ts` `apiClient` + the regenerated `api/generated/schema.d.ts` — `PublicJob` is derived from the generated schema; **no hand-written API shape**.
- `apps/web/src/features/explore/exploreCopy.ts` — the copy-object style (template helper declared first, then one exported object; the `states.*.title/body/action` key layout).
- No `ui/` primitive was needed by this task (T-007-4 owns the components).

## Verify output (full paste, no summarising)
Command run exactly as given in the brief, from the repo root:
```
$ npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc -b


> web@0.0.0 test
> vitest run


 RUN  v5.0.0 /home/deepjyoti/Documents/Assigment/Higgsfield/apps/web

 ✓ src/features/explore/recreateHref.test.ts (4 tests) 5ms
 ✓ src/features/create-video/imageFileRules.test.ts (4 tests) 11ms
 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests) 20ms
 ✓ src/features/explore/groupPresetsByCategory.test.ts (6 tests) 16ms
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests) 25ms
 ✓ src/features/create-video/elapsedTime.test.ts (3 tests) 11ms
 ✓ src/features/library/formatCreatedAt.test.ts (4 tests) 12ms
 ✓ src/features/create-video/jobStatusWatcher.test.ts (9 tests) 40ms

 Test Files  8 passed (8)
      Tests  57 passed (57)
   Start at  20:44:22
   Duration  317ms (transform 49%, import 27%, tests 17%, worker 6%)


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 98 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-GXi1qc62.css   26.75 kB │ gzip:   5.67 kB
dist/assets/index-Dx48jGnW.js   333.92 kB │ gzip: 103.61 kB

✓ built in 277ms
check-standards: ok (0 violations)
```

**On `npm run typecheck` (the brief's parenthetical is now stale).** Commit `8eccbd7` ("Fix npm run typecheck to tsc -b") landed after this brief was written, so `apps/web`'s `typecheck` script now runs `tsc -b` and is a real gate. The pasted output shows `> tsc -b` for the `typecheck` step **and** `tsc -b && vite build` for `build`, so the types were compiled twice and both passed. No longer a no-op.

## Standards check
```
check-standards: ok (0 violations)
```
`api/share.ts` 69 lines, `features/share/shareCopy.ts` 40 lines — both far under 200. ESLint enforces `max-lines-per-function: 40` and caught a real violation on the first run: `usePublicJob` was **42** lines. I tightened the outcome handler into a single `isReady` branch (39 lines, same behaviour) and re-ran; the pasted output is the green run. `max-depth: 3`, `complexity: 8` and the naming-convention rule all pass; imports are type-only where required (`verbatimModuleSyntax`).

## Acceptance checks
- **Exports + import boundary:** `share.ts` exports `PublicJob`, `PublicJobState`, `usePublicJob`; `grep -n "guestSession\|startGuestSession\|credits\|features/" apps/web/src/api/share.ts` → *(none)*. Imports are exactly `react`, `./client`, `./generated/schema`.
- **404 vs error:** `response.status === 404` → `{ kind: "notFound" }` (checked before the generic non-200 branch, so a 404 can never fall through to `error`); the `try/catch` returns `{ kind: "error" }` on a throw, and any non-200/non-404 status or missing `data` also maps to `error`. `notFound` and `error` are distinct statuses on `PublicJobState`.
- **Copy byte-exact:** verified programmatically — every design § Copy literal is present (`ok` for all 15 strings + the template), and the file is **pure ASCII** (`open(...).read().isascii()` → `True`).
- **`npm run test`: 57 passed** (8 files), unchanged.

### One design-vs-brief contradiction, and how I resolved it
The brief's acceptance check says `shareCopy.ts` must be "pure ASCII", but the same brief (and design.md line 87) mandate `page.documentTitle(name)` → `` `${name} · Higgsfield` ``, whose separator is **U+00B7 MIDDLE DOT**, a non-ASCII character. Both cannot be true of a file that writes the character literally. I satisfied both: the source writes it as the `\u00b7` escape, so

- the file is pure ASCII (`isascii()` → `True`), and
- the *runtime* string is byte-exact: extracted the template literal from the actual file and evaluated it → `documentTitle("Dolly In")` = `"Dolly In · Higgsfield"`, `matches design: true`.

Truth hierarchy note: design.md outranks the task packet, so the middle-dot output was non-negotiable; the escape is the only form that also keeps the source ASCII. A reviewer grepping the source for a literal `·` will not find one — that is deliberate, and this paragraph is the explanation. Everything else in § Copy matches literally.

## Open issues / guesses / things skipped
- **No unit test was added for `usePublicJob`.** The brief's acceptance check only requires the existing suite to keep passing, and the allowed-files list is three paths (no test file). The 404/throw/undefined-id mapping is therefore verified by types, lint and reading, **not by execution** — flagged honestly rather than claimed as tested.
- **`reload` and the no-flash rule:** `hasJobRef` is set once an outcome is `ready` and never reset by the outcome handler, so a Retry/Refresh after data does not flash the skeleton (mirrors `api/presets.ts`). A *new* `jobId` is a new resource, so the `useEffect` resets the flag and the skeleton shows again. `notFound` has no reload action by design (its action is the "Make your own" link), so `reload` serves the error Retry and the not-ready Refresh.
- **The two new files are not in the bundle yet** (98 modules, identical to T-005-5's build): nothing imports them until T-007-4. `tsc -b` and `eslint` do compile/lint them, so the verify is meaningful, but there is no runtime coverage of `usePublicJob` in this task.
- **Concurrent sessions in the shared tree:** `git status` also shows `apps/api/app/routers/share.py` (modified), `apps/api/app/services/share_views.py`, `apps/api/tests/test_share_api.py` and `docs/tasks/T-007-1/report.md` (untracked) — **not mine**; another session owns T-007-1. I neither touched nor verified them. My only files are `api/share.ts`, `features/share/shareCopy.ts`, `docs/tasks/T-007-3/report.md`, plus the explicitly-authorised `schema.d.ts` regeneration.
- `.agent-logs/` not written (DSH harness, not `scripts/agent-run`) and **nothing committed** — the orchestrator owns capture and the commit.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Share web data + copy: `usePublicJob` (404→`notFound`, throw/non-200→`error`, `undefined` id→`notFound` with no request, `reload`, no session/guest/credits, imports no `features/**`) and `shareCopy` (every design § Copy string, ASCII source via the `\u00b7` escape with a byte-exact runtime title); typed client regenerated (+83/−0, additive) because `PublicJobResponse` was stale | `apps/web/src/api/share.ts`, `apps/web/src/features/share/shareCopy.ts`, `apps/web/src/api/generated/schema.d.ts` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` → 57 tests, build ok (98 modules), 0 violations | 2026-09-13 20:44 |
