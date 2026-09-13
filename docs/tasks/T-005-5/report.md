# Report T-005-5

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `apps/web/src/App.tsx`: added one import (`import { LibraryPage } from "./features/library/LibraryPage"`) and changed the `library` route from `<Placeholder title="Library" />` to `<LibraryPage />`. Every other route, the `Placeholder` component and its use by `create/image` and `credits`, the `EmptyState` share placeholder and all other imports are untouched (file 53 → 54 lines).
- `docs/tasks/T-005-5/report.md`: this report.

## Reused
- Nothing new: the page, hook and copy were all built by T-005-2/T-005-3/T-005-4. This task only wires the existing `LibraryPage` into the existing router.
- The route shape (nested under the `AppShell` layout route with the session as `outletContext`) is unchanged — `LibraryPage` reads it with `useOutletContext<SessionContextValue>()`.

## Verify output (full paste, no summarising)
Command run exactly as given in the brief, from the repo root:
```
$ npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc -b


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

✓ built in 319ms
check-standards: ok (0 violations)
```
Note: `LibraryPage` is now in the bundle — **98** modules vs **89** before this route was wired (T-005-4's report recorded 89, accurate at the time). `tsc -b` is the real type gate and it ran and passed.

## Standards check
```
check-standards: ok (0 violations)
```
`App.tsx` = 54 lines. No function over 40 lines; eslint (`max-lines`, `max-lines-per-function`, `max-depth`, `complexity`, naming-convention) passed as part of `lint`.

## Manual check (curl; the accepted substitute for a browser pass)
Environment: this CLI session has **no browser**, so the brief's "curl-level check plus a bundle grep" substitute was used. `docker compose ps` showed `db` and `minio` up (healthy) and a DB-backed API already running on port 8000 (`uvicorn app.main:app --reload`, cwd `apps/api`, `GET /api/health` → 200 `{"status":"ok","database":"ok"}`). Port 8000 was occupied by that same repo API, so I used it instead of starting a second server on an occupied port; `--reload` means it is running current code, and `static_dir` is read per request, so it served the shell that this task's build just produced. The brief's `docker compose up -d --wait db` + `alembic upgrade head` were run/verified (`alembic upgrade head` exited 0, no pending output).

```
### signed-out GET /api/v1/jobs (expect 401)
HTTP/1.1 401 Unauthorized
date: Sun, 13 Sep 2026 15:12:19 GMT
server: uvicorn
content-length: 26
content-type: application/json

{"detail":"Not signed in"}

### GET /library (expect 200 + index.html shell)
HTTP/1.1 200 OK
date: Sun, 13 Sep 2026 15:12:19 GMT
server: uvicorn
content-type: text/html; charset=utf-8
accept-ranges: bytes
content-length: 748
last-modified: Sun, 13 Sep 2026 15:12:04 GMT
etag: "17266b38b34ad3dc6b3229e586cfbe56"

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <title>Higgsfield</title>
    <script type="module" crossorigin src="/assets/index-Dx48jGnW.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index-GXi1qc62.css">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```
The served shell references `index-Dx48jGnW.js`, i.e. the asset hash this task's `npm run build` just emitted — so `/library` is served by the current build, not a stale one. Bundle grep of that served asset:
```
$ curl -s http://127.0.0.1:8000/assets/index-Dx48jGnW.js -o /tmp/lib-bundle.js && wc -c /tmp/lib-bundle.js
333927 /tmp/lib-bundle.js
$ for s in "Everything you have generated." "No generations yet." "We couldn't load your library." "This generation is no longer available." "Make another"; do grep -c -F "$s" /tmp/lib-bundle.js; done
1   # Everything you have generated.
1   # No generations yet.
1   # We couldn't load your library.
1   # This generation is no longer available.
1   # Make another
```
So the deployed bundle actually contains the Library copy, and the route resolves to it. What this does **not** prove is the in-browser render (skeleton swap, `?job=` selection writing history, video playback) — that remains for the browser-level `verify-slice` pass.

## Cross-check of T-005-1…T-005-4 reports against the code
Every substantive claim holds; one is now stale, and the truth hierarchy says the code wins:

- **T-005-1** — `list_owned_jobs` exists in `repositories/jobs.py:57`; `LibraryItemView`/`list_owned_jobs_view`/`_library_item_view`/`_referenced_asset_ids` exist in `services/job_views.py`; `list_jobs` keeps `response_model=LibraryListResponse` and `limit: Annotated[int, Query(ge=1, le=100)] = 50` (`routers/jobs.py:90,98`); `test_library_api.py` has exactly 7 tests; `thumbnail_url=poster_url or input_url` (poster → input → `None`) and `preset_names.get(job.preset_slug, job.preset_slug)` (slug fallback) both match the report. **No mismatch.**
- **T-005-2** — `features/create-video/useGuestSessionRunner.ts` is deleted (no longer tracked); `api/guestSession.ts` and `api/library.ts` match the described shapes and import no `features/**`. The `LibraryItemResponse`/`LibraryListResponse` types are in the generated schema. **No code mismatch.**
- **T-005-3** — `libraryCopy.ts` carries every design § Copy string plus `time.label`; `formatCreatedAt.ts` renders UTC and normalises ICU `"Sept"` → `"Sep"`; `formatCreatedAt.test.ts` has 4 tests. **No mismatch.**
- **T-005-4** — the six files exist with the described responsibilities; `grep -rn "jobs/" apps/web/src/features/library/` still returns nothing (no second API call); the only widened item vs the design Props table (`LibraryResultView` accepts `null` for the AC-7 missing panel) is disclosed in that report. **No mismatch.**
- **Stale claim (report vs code):** T-005-2, T-005-3 and T-005-4 all state "`npm run typecheck` is a known no-op (`tsc --noEmit`)". Commit `8eccbd7` ("Fix npm run typecheck to tsc -b") landed after those reports and `apps/web/package.json` now runs `tsc -b`, as this task's verify output shows. Those three reports' rationale is therefore historical; the type gate is now the `typecheck` script *and* `tsc -b` inside `build`. Nothing to fix in code — flagged for the docs sync in `docs/PLAN.md`/`docs/STANDARDS.md`.
- Per the brief I did **not** fix anything in `features/library/**`, `api/**`, `ui/**`, the API or the contract; nothing needed it.

## Open issues / guesses / things skipped
- **No browser**, as above: route + served-shell + bundle-grep evidence only; the AC-2/AC-5/AC-11 in-browser pass is left to `verify-slice`.
- **I used the already-running API on :8000 rather than starting a new uvicorn**, because the port was occupied by the same repo's `uvicorn app.main:app --reload` (DB healthy). Starting a second one would have failed on the port; killing another session's server was not mine to do.
- **`.agent-logs/` not written** (DSH harness, not `scripts/agent-run`) and **nothing committed** — orchestrator owns capture and the commit. `git status --short` shows only `apps/web/src/App.tsx` + this report.
- No file over 200 lines, no function over 40 lines; `scripts/check-standards` → 0 violations.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Library assembled: the `library` route renders `LibraryPage` inside `AppShell` (98-module bundle; signed-out `/library` serves the built shell, `GET /api/v1/jobs` → 401 with no cookie) | `apps/web/src/App.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → build ok (98 modules), 0 violations; `curl -s -i http://127.0.0.1:8000/api/v1/jobs` → 401 `{"detail":"Not signed in"}`; `curl -s -i http://127.0.0.1:8000/library` → 200 index.html referencing `/assets/index-Dx48jGnW.js`; served bundle contains the Library copy (browser AC pass deferred to `verify-slice`) | 2026-09-13 20:42 |
