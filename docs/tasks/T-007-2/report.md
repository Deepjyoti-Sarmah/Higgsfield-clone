# Report T-007-2

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `apps/api/app/services/share_html.py` (new, 90 lines): the pure HTML/meta layer. `FALLBACK_SHELL` (a minimal built-in document) + `read_shell(static_dir)` (reads the built `index.html`, falls back on any `OSError`); `share_url_for(base_url, job_id)`; `page_title(view)` → `"{preset_name} · Higgsfield"` or `"Higgsfield"`; `describe_public_job(view)` → the four design § Copy strings by status (succeeded names the preset, queued/running, failed, unknown); `meta_tag(attribute, key, value)` (every value `html.escape(..., quote=True)`); `build_meta_block(view, share_url)`; `inject_meta(shell, title, meta_block)` (two string ops: `<title>…</title>` regex replace, then insert the block before `</head>`); `render_share_page(...)`.
- `apps/api/app/routers/share_page.py` (new, 42 lines): `GET /v/{job_id}` with `response_class=HTMLResponse` and **`include_in_schema=False`**. `job_id` is typed `str` and parsed by `parse_job_id`, so a malformed id renders the generic page instead of FastAPI returning a JSON **422** — the route always answers HTML 200. Uses the same `Depends` providers as the JSON share route (`get_session`, `get_object_storage`, `get_settings`) and calls T-007-1's `share_views.read_public_job` unchanged.
- `apps/api/app/main.py` (edit, 57 → 60 lines): added `share_page` to the routers import and `app.include_router(share_page.router)` **immediately before `mount_single_page_app(...)`**, with a two-line comment saying why the order is load-bearing.
- `apps/api/tests/test_share_page.py` (new, 189 lines): 6 tests covering no-cookie meta tags, succeeded video/image tags, unknown **and** malformed ids, the failed copy with no private error text, preset-name escaping, and the missing-index fallback shell.
- `docs/tasks/T-007-2/report.md`: this report.

## Reused
- `apps/api/app/services/share_views.py` (`read_public_job`, `PublicJobView`) — imported, never changed; its `_ready_url` rule means only **ready** assets produce `poster_url`/`video_url`, so `og:image`/`og:video` appear only when those assets exist.
- `apps/api/app/routers/share.py`'s dependency set and `app.db.get_session`, `app.storage_dependencies.get_object_storage`, `app.settings.get_settings` — the exact providers the JSON route uses.
- `tests/job_api_helpers.py` (`create_queued_job`, `current_user_id`, `PRESET_NAME`), `tests/fakes/in_memory_object_storage.py`, and the `app`/`client`/`guest_client`/`object_storage`/`session_maker` fixtures from `conftest.py`.
- `mount_single_page_app` — the new route only *precedes* it; the SPA catch-all still serves every other path.

## Verify output (full paste, no summarising)
Command run exactly as given in the brief, from the repo root. The steps are separated with their exit codes because the whole chain is `&&`-joined and I wanted per-step evidence:
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
docker exit=0

$ uv --directory apps/api run ruff check .
All checks passed!
ruff exit=0

$ uv --directory apps/api run mypy
Success: no issues found in 31 source files
mypy exit=0

$ uv --directory apps/api run pytest -q
........................................................................ [ 56%]
........................................................                 [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
128 passed, 2 warnings in 41.66s
pytest exit=0

$ scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
wrote packages/contracts/openapi.json
export exit=0
contract-diff exit=0

$ scripts/check-standards
check-standards: ok (0 violations)
standards exit=0
```
`git diff --exit-code packages/contracts/openapi.json` exited **0**: the HTML route is `include_in_schema=False` and the contract stayed **byte-identical** after re-export (AC-11).

Two honest notes on getting to this run:
- **The first full-suite run failed on the known pre-existing flake**, `tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` (it claimed another test's leftover step: `second.job_id != job_id`). Isolated re-run → `1 passed in 0.76s`; the green full run above followed. This is the exact flake already documented in `docs/STATUS.md` (BROKEN) and not caused by this change (nothing here claims steps or touches the reaper).
- **`check-standards` initially flagged `tests/test_share_page.py` at 208 lines (max 200).** I compacted the helpers (one loop over an `OUTPUT_ASSETS` tuple, the preset rename inlined) and merged the unknown-id and malformed-id tests into one → **189 lines**, standards green.

## Standards check
```
check-standards: ok (0 violations)
```
File sizes: `share_html.py` 90 · `share_page.py` 42 · `main.py` 60 · `test_share_page.py` 189 — all ≤ 200. Functions are all well under 40 lines; ruff `C90` (max complexity 8) passes, so `build_meta_block`/`describe_public_job` are within budget. `mypy --strict` is green over `app/services` (31 files), so `share_html.py` is fully typed. No new dependency; injection is `re.sub` + `str.replace`.

## Manual / live evidence (beyond the ASGI tests)
The repo's `uvicorn app.main:app --reload` on :8000 picked up the change. With the built shell present (`apps/web/dist`), a no-cookie request returns the real shell **with** the meta block — which proves the route precedes the SPA catch-all (the catch-all would serve the bare shell with no OG tags):
```
$ curl -s -i http://127.0.0.1:8000/v/not-a-uuid
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
...
    <title>Higgsfield</title>
    <script type="module" crossorigin src="/assets/index-DRwkTUYF.js"></script>
      <meta property="og:title" content="Higgsfield" />
    <meta property="og:description" content="Watch AI-generated videos on Higgsfield." />
    <meta property="og:type" content="video.other" />
    <meta property="og:site_name" content="Higgsfield" />
    <meta property="og:url" content="http://127.0.0.1:8000/v/not-a-uuid" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="Higgsfield" />
  </head>
$ grep -c "favicon.svg"  /tmp/vpage.html   # built shell
1
$ grep -c "assets/index-" /tmp/vpage.html  # built shell (js + css)
2
```
Then I created a **real** job over the live API (guest → presigned upload → complete → `POST /jobs`, status `queued`) and fetched its `/v/<id>` with no cookie:
```
$ curl -s -i http://127.0.0.1:8000/v/52f42ca1-a49e-4a1e-8407-e850df1eb7d6
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
    <title>Dolly In · Higgsfield</title>
      <meta property="og:title" content="Dolly In · Higgsfield" />
    <meta property="og:description" content="This video is still being generated on Higgsfield." />
    <meta property="og:type" content="video.other" />
    <meta property="og:url" content="http://127.0.0.1:8000/v/52f42ca1-a49e-4a1e-8407-e850df1eb7d6" />
    <meta name="twitter:card" content="summary_large_image" />
$ curl -s .../v/$JOB | grep -c "secret prompt text"   # the job's private prompt
0
```
So a real queued job gets the DB preset name in `<title>`/`og:title`, the queued description, `og:url` from `request.base_url`, no `og:video`/`og:image`, and no private data (AC-8).

## Acceptance checks
- **Real job id, no cookie → 200 `text/html` + `<title>`/og tags** — live curl above and `test_no_cookie_gets_html_with_the_job_meta_tags`.
- **Succeeded adds `og:video` + `og:image`; queued has neither `og:video` nor `<video>`** — `test_succeeded_job_adds_the_video_and_image_tags` (ready video+poster assets) asserts `og:video`, `og:image`, `twitter:image`, `twitter:card=player`, and the presigned `?get` URLs; the queued test asserts `og:video`/`<video` absent.
- **Unknown uuid → 200 generic meta, not 500/404** — `test_unknown_or_malformed_id_returns_generic_html` (also covers a non-uuid path, which with a `uuid.UUID` path param would have been a JSON 422; `parse_job_id` keeps the HTML contract).
- **Escaping** — `test_preset_name_is_escaped_inside_content_attributes` sets the preset name to `Bad "Name" <script>alert(1)</script>`, then asserts the raw string is absent, `&lt;script&gt;`/`&quot;Name&quot;` are present, and `content="Bad "Name"` never appears (no attribute break-out).
- **Fallback shell** — `test_missing_index_falls_back_to_the_builtin_shell` overrides `static_dir` with an empty `tmp_path`; still 200 HTML with og tags and exactly one `</head>`.
- **Contract byte-identical** — `export-openapi && git diff --exit-code` → exit 0.
- **ruff + mypy + full suite green** — see the verify output (128 passed).

## Open issues / guesses / things skipped
- **`html.escape(quote=True)` also escapes `'` → `&#x27;`.** The failed-state copy contains an apostrophe ("This video isn't available…"), so the rendered attribute is `This video isn&#x27;t available…`. That is correct HTML and valid in a double-quoted attribute; the test compares against `escape(FAILED_DESCRIPTION, quote=True)` rather than the raw string. Worth knowing for anyone grepping the rendered HTML for the raw copy.
- **`twitter:image` is emitted only when a poster exists** (same condition as `og:image`). Design § The route lists `twitter:image` among the tags but conditions only `og:image` explicitly; spec AC-7 conditions `og:image` on the poster and does not require `twitter:image`. Emitting an image tag with an empty `content` would be worse, so it follows the poster. Flagging the reading rather than silently choosing.
- **No `<video>` element is ever injected** — the route only writes `<head>` meta. The body stays exactly the shell, so "a queued job has no `<video>`" is true for every status; the video itself is rendered client-side by T-007-4.
- **`job_id` is typed `str`, not `uuid.UUID`.** This is deliberate (always-200 HTML contract) and is the one place I chose robustness over the design's "path `job_id` (uuid)" table note for the *JSON* route; the JSON route still types it `uuid.UUID` and still 422s. `parse_job_id` returns `None` → generic meta, never a 500.
- **`og:url` uses `str(request.base_url).rstrip("/")`**, so a proxied request's forwarded host is respected (the design's noted cosmetic risk). `og:image`/`og:video` are the absolute URLs T-007-1 builds (presigned or `S3_PUBLIC_BASE_URL`-joined).
- **Concurrent sessions in the shared tree:** `apps/web/src/features/share/{SharePage,ShareResult,ShareStates}.tsx` and `docs/tasks/T-007-4/report.md` are untracked and **not mine** (T-007-4). I did not touch or verify them; they do not affect this task's API-only verify.
- `.agent-logs/` not written (DSH harness, not `scripts/agent-run`) and **nothing committed** — the orchestrator owns capture and the commit.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| `GET /v/{job_id}` HTML share route: registered **before** the SPA catch-all, `include_in_schema=False`; reads the built shell (built-in fallback), replaces `<title>` and injects escaped `og:*`/`twitter:*` tags (image/video only when those ready assets exist, `twitter:card` player vs summary_large_image); always 200 HTML, even for unknown/malformed ids; no private fields | `apps/api/app/routers/share_page.py`, `apps/api/app/services/share_html.py`, `apps/api/app/main.py`, `apps/api/tests/test_share_page.py` | `docker compose up -d --wait db && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` → 128 passed, mypy clean (31 files), contract byte-identical, 0 violations; live: no-cookie `GET /v/<real queued job>` → 200 `text/html` with `<title>Dolly In · Higgsfield</title>` + og tags and no private prompt | 2026-09-13 22:08 |
