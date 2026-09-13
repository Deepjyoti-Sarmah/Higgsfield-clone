# Report T-007-5

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `apps/web/src/App.tsx` (edit, 54 → 47 lines): added `import { SharePage } from "./features/share/SharePage"` and replaced the `v/:jobId` placeholder `EmptyState` with `<Route path="v/:jobId" element={<SharePage />} />`. Nothing else changed — the exact diff is:
```diff
@@ -7,6 +7,7 @@ import { LibraryPage } from "./features/library/LibraryPage"
 import { GuestButton } from "./features/session/GuestButton"
 import { SessionBadge } from "./features/session/SessionBadge"
 import { useSession } from "./features/session/useSession"
+import { SharePage } from "./features/share/SharePage"
@@ -39,15 +40,7 @@ export function App() {
         <Route path="library" element={<LibraryPage />} />
         <Route path="credits" element={<Placeholder title="Credits" />} />
-        <Route
-          path="v/:jobId"
-          element={
-            <EmptyState
-              title="Share page"
-              description="Public share pages are coming soon."
-            />
-          }
-        />
+        <Route path="v/:jobId" element={<SharePage />} />
       </Route>
```
  The `index`, `create/video`, `create/image`, `library` and `credits` routes, the `AppShell` wiring (`rightSlot` + `outletContext`), `Placeholder` and the `EmptyState` import (still used by `Placeholder`) are all untouched.
- `docs/tasks/T-007-5/report.md`: this report.

## Reused
- `apps/web/src/features/share/SharePage.tsx` (T-007-4) — the route now renders it as-is; no edit to any `features/share/**` file.
- The existing `AppShell` layout route: `/v/:jobId` stays a child of it, exactly like every other route, so the design's App.tsx row is satisfied without restructuring.
- No new dependency, no `ui/**` or `api/**` change.

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
✓ 103 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-Cajc0ZMs.css   26.85 kB │ gzip:   5.67 kB
dist/assets/index--wlTazLa.js   337.38 kB │ gzip: 104.39 kB

✓ built in 175ms
check-standards: ok (0 violations)
```
`SharePage` is now in the bundle: **103** modules vs **98** before this route was wired (T-007-4 recorded 98, accurate then — its three files were still tree-shaken because nothing imported them). `tsc -b` is the real type gate.

**The brief's parenthetical "(npm run typecheck is a known no-op in this repo)" is stale.** Commit `8eccbd7`/`T-000-6` changed the script to `tsc -b`, so the `typecheck` step above is a real gate (and `build` runs `tsc -b` again). Confirmed by the `> tsc -b` line in the output.

## Standards check
```
check-standards: ok (0 violations)
```
`App.tsx` = 47 lines; no function over 40 lines; eslint (`max-lines`, `max-lines-per-function`, `max-depth`, `complexity`, naming-convention) passed as part of `lint`.

## Public no-JS check (required — done with curl)
Setup: `docker compose up -d --wait db` → healthy; `uv --directory apps/api run alembic upgrade head` → `exit 0`; a repo `uvicorn app.main:app --reload` was already listening on `:8000` (`/api/health` → 200) and serves the freshly built `dist` (static files are read per request), so no second server was started on the occupied port.

Guest + job created **with curl** (201 guest → 201 upload → 200 PUT → 200 complete → 202 job):
```
1) guest:          HTTP 201
2) upload request: HTTP 201
3) PUT bytes:      HTTP 200
4) complete:       HTTP 200
5) create job:     HTTP 202   job_id=19cefb14-0832-46fe-a928-f5da70fefa6a status=queued
```
The share URL fetched with **no cookie jar, no `-b` flag and no JavaScript** — the brief's exact command:
```
$ curl -s http://localhost:8000/v/19cefb14-0832-46fe-a928-f5da70fefa6a | \
    grep -Eo '<title>[^<]*</title>|property="og:[a-z:]+"|name="twitter:card"'
<title>Dolly In · Higgsfield</title>
property="og:title"
property="og:description"
property="og:type"
property="og:url"
name="twitter:card"
```
Every required tag is present: `<title>`, `og:title`, `og:description`, `og:url`, `twitter:card` (plus `og:type`). Response line: `HTTP 200  content-type=text/html; charset=utf-8`. To prove no cookie was involved, the verbose request headers show only the request line and Host — there is no `Cookie:` header:
```
$ curl -sv http://localhost:8000/v/19cefb14-... -o /dev/null 2>&1 | grep -E '^> (GET|Cookie|Host)'
> GET /v/19cefb14-0832-46fe-a928-f5da70fefa6a HTTP/1.1
> Host: localhost:8000
```
Unknown uuid → **200** with generic meta:
```
$ curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/v/11111111-1111-4111-8111-111111111111
200
$ curl -s http://localhost:8000/v/11111111-1111-4111-8111-111111111111 | \
    grep -Eo '<title>[^<]*</title>|property="og:[a-z:]+"|name="twitter:card"'
<title>Higgsfield</title>
property="og:title"
property="og:description"
property="og:type"
property="og:url"
name="twitter:card"
```
Privacy spot-check: the job's private prompt (`no-js check prompt`) appears **0** times in the share HTML.
```
$ curl -s http://localhost:8000/v/19cefb14-... | grep -c "no-js check prompt"
0
```

**Browser check: SKIPPED — this CLI session has no browser.** The accepted substitute is used: the curl above (server-rendered tags, no JS/cookie), plus a bundle grep of the asset the shell actually serves, which shows the routed `SharePage` copy is in the browser bundle:
```
$ curl -s http://localhost:8000/v/19cefb14-... | grep -o '/assets/index-[^"]*\.js'
/assets/index--wlTazLa.js
$ curl -s http://localhost:8000/assets/index--wlTazLa.js -o /tmp/t007-5-bundle.js && wc -c /tmp/t007-5-bundle.js
337389 /tmp/t007-5-bundle.js
$ for s in "Made with Higgsfield" "Make your own" "Still generating." \
           "This video doesn't exist or was removed." "Loading this video" "Download"; do grep -c -F "$s"; done
1   # Made with Higgsfield
1   # Make your own
1   # Still generating.
1   # This video doesn't exist or was removed.
1   # Loading this video
1   # Download
```
What this does **not** prove is the in-browser render (skeleton swap, video playback, `document.title` update); that remains for a browser-level `verify-slice` pass.

## Cross-check of T-007-1…T-007-4 reports against the code
All substantive claims match the running code; the only stale items are historical counts, and one brief-level note.

- **T-007-1** — `routers/share.py` keeps `read_public_job` / `response_model=PublicJobResponse` / `responses={404: ...}` / `job_id: uuid.UUID`; `services/share_views.py` reads only the two **output** asset ids (input never fetched) and mirrors the ready-only `_ready_url` rule; `tests/test_share_api.py` has exactly 7 tests. Its `mypy 30 files` / `122 passed` were correct then and have simply grown (31 files, 128 tests) as T-007-2 added `share_html.py` + 6 tests. **No mismatch.**
- **T-007-2** — `share_html.py` + `share_page.py` exist as described, `share_page.router` is included immediately before `mount_single_page_app` in `main.py`, and the route is `include_in_schema=False`. **No mismatch.**
- **T-007-3** — `api/share.ts` exports `PublicJob`/`PublicJobState`/`usePublicJob` with 404→`notFound`, non-200/throw→`error`, no session/guest/credits imports; `shareCopy.ts` matches design § Copy. **No mismatch.**
- **T-007-4** — `ShareStates.tsx` has all five states (loading `aria-busy` + `srText`, error Retry, notReady Refresh, notFound/failed → `ButtonLink` to `page.ctaHref`); `ShareResult.tsx` renders the preset name as the only `h1`, `<video controls muted playsInline loop preload="metadata">` with the poster, the attribution, the Download anchor and "Make your own", and no `<video>`/Download when `video_url` is null; `SharePage.tsx` maps `ready`+`succeeded` → `ShareResult` and everything else through `resolveState`, with `document.title` restored on unmount. Its `98 modules` line is a historical pre-route count (now 103) — a consequence of this task, not an error. **No mismatch.**
- **Stale claim worth recording:** T-007-3/R4 (and this task's brief) call `npm run typecheck` a no-op, but the script is `tsc -b` since `8eccbd7`; the verify output above shows it as a real gate.

Per the brief I did **not** fix anything in `features/share/**`, `api/**`, `ui/**`, the API or the contract; nothing needed it.

## Open issues / guesses / things skipped
- **No browser**, as above: server-rendered HTML + bundle grep only; the in-browser AC pass is left to `verify-slice`.
- **`/v/:jobId` still renders inside `AppShell`** (nav + guest/session header), like every other route — the design's App.tsx row only says `v/:jobId` → `SharePage`, so this is intended, not an oversight. The public *HTML* route (T-007-2) is what crawlers read; a signed-out visitor's `useSession()` only probes `/api/v1/me` (401 → signed-out) and never bootstraps a guest, so AC-9 (read-only, no session created) still holds on the client.
- I used the already-running `uvicorn --reload` on `:8000` rather than starting a second server, because the port was occupied by this repo's own API (healthy DB) and `static_dir` is read per request.
- `.agent-logs/` not written (DSH harness, not `scripts/agent-run`) and **nothing committed** — the orchestrator owns capture and the commit. `git status --short` shows only `apps/web/src/App.tsx` plus this report.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Share page assembled: `v/:jobId` renders `SharePage` (103-module bundle, was 98); no-JS public check passes — a real queued job's `/v/<id>` with no cookie returns 200 `text/html` carrying `<title>Dolly In · Higgsfield</title>`, `og:title`, `og:description`, `og:type`, `og:url`, `twitter:card`, and an unknown uuid returns 200 with generic meta; the private prompt never appears | `apps/web/src/App.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → 103 modules, 0 violations; curl no-cookie `GET /v/<real job>` → 200 + meta tags; `curl -w '%{http_code}' /v/<unknown-uuid>` → 200 (browser AC pass deferred to `verify-slice`) | 2026-09-13 22:13 |
