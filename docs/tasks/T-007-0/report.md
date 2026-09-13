# Report T-007-0

**Agent / model / tool:** orchestrator/designer · deepseek-flash · DeepSeek Harness (DSH), working directly
**Result:** DONE — spec 007 designed, tasks split, and the one new public route published as a schema + 501 stub + regenerated `openapi.json`

## Files changed
| File | New/Edit | What |
|---|---|---|
| `docs/specs/007-share/spec.md` | New | story, AC-1…AC-11, all four UI states, out of scope (revocable links / social layer / generated OG images deferred), open questions |
| `docs/specs/007-share/design.md` | New | AC→design→task map, the contract change, the **OG/meta approach**, data (no migration), flow, component tree, copy tables (client + server), Files table with task owners, reused, risks |
| `docs/specs/007-share/tasks.md` | New | T-007-0 (ticked) + T-007-1…T-007-5 with disjoint files, waves, verify commands |
| `docs/tasks/T-007-1/brief.md` … `T-007-5/brief.md` | New | five filled briefs from `docs/templates/delegation-brief.md` |
| `apps/api/app/schemas/share.py` | New | `PublicJobResponse` — the frozen public shape |
| `apps/api/app/routers/share.py` | New | the public JSON route as a 501 stub |
| `apps/api/app/main.py` | Edit | include the share router (before the SPA catch-all) |
| `packages/contracts/openapi.json` | Edit | regenerated |
| `docs/tasks/T-007-0/report.md` | New | this report |

No other file was touched. **This commit deliberately excludes the in-flight `T-005-1`/`T-005-2`/`T-005-3` working-tree changes** (the Library API, the web data layer and the copy/helper) — those are staged for their own commit and were verified green in the previous wave.

## The two design questions, answered

**(a) How the API exposes a job publicly.** A new route, `GET /api/v1/public/jobs/{job_id}`, rather than widening the existing `GET /api/v1/jobs/{job_id}`. The existing route is owner-scoped (404 for anyone else) and its `JobResponse` carries exactly what must not be public: the owner, the user's `prompt`, `credit_cost`, asset ids and the internal `error_message`. The new route has **no auth dependency**, so `openapi.json` shows it with no security scheme, and its shape is the seven public fields only. It answers **200 for any existing job whatever its status** (the page renders "still generating"/"failed" itself) and **404** only for an unknown id, so a holder of the link gets a state, not an error.

**(b) How OG tags get served.** The SPA cannot provide them: `main.py`'s catch-all serves the same `index.html` for every path and crawlers do not run JS. So a new `GET /v/{job_id}` route in `routers/share_page.py` (T-007-2) is registered **before** `mount_single_page_app` — Starlette matches in registration order, so it wins for that path only — reads the built shell from `settings.static_dir`, replaces `<title>` and inserts the meta block before `</head>`, and returns `HTMLResponse`. It is `include_in_schema=False`, so the JSON contract does not move. It always answers 200 (generic meta for an unknown id) so the client can render its not-found state, and it falls back to a built-in shell when `index.html` is absent, so the API never 500s and tests do not depend on `npm build`.

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
/api/v1/public/jobs/{job_id}
/api/v1/uploads
/api/v1/uploads/{asset_id}/complete
$ ls docs/tasks | grep T-007
T-007-1
T-007-2
T-007-3
T-007-4
T-007-5
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Extra verification (beyond the brief's command)
- **The contract only grew:** `git diff --stat packages/contracts/openapi.json` → **118 insertions(+), 0 deletions**; a filter for deletions prints `NO DELETIONS ✓`. Re-running `scripts/export-openapi` leaves the file unchanged, so the frozen contract is stable.
- **The new route is genuinely public:** in `openapi.json` the operation `read_public_job_api_v1_public_jobs__job_id__get` has **no `security` key** and only the `job_id` path param (no session cookie), `200 → PublicJobResponse`, plus `404`/`422`. `PublicJobResponse` has exactly `created_at, id, poster_url, preset_name, preset_slug, status, video_url` — **no owner, prompt, credits, asset ids or error text**.
- **The stub behaves as designed** (ASGI client, local Postgres): no cookie → **`501 {"detail":"Not implemented"}`** (not 401 — proving it is unauthenticated); a malformed uuid → **422**.
- **Baseline for the OG work:** `GET /v/<uuid>` currently returns **200 `text/html`** — i.e. the generic SPA shell, exactly the problem T-007-2 fixes; its curl assertion will show the difference.
- **Disjointness** (script over `tasks.md`): 14 file entries, 12 distinct. The only shared files are the two **declared sequential hand-offs** from this designer task — `routers/share.py` (T-007-0 → T-007-1, waves 0→1) and `main.py` (T-007-0 → T-007-2, waves 0→2). **No same-wave clash.**

## Open issues / guesses / things skipped
1. **Secret-link semantics.** The share key is the job's UUIDv4, so anyone with the link can view and there is no revocation in P0. A `share_token` column plus a migration is the P1 answer; recorded in the spec.
2. **Presigned URLs expire (1 h) while a preview card can be cached for days.** `og:image`/`og:video` point at presigned URLs, so a crawled card may hold an expired image. The P0 mitigation already in the codebase is a stable `S3_PUBLIC_BASE_URL`; a permanent media route is P1. Flagged in the design's risks.
3. **`/v/{unknown}` answers 200, not 404.** Deliberate: a 404 status would replace the app shell in some browsers/crawlers and give a worse not-found experience than the rendered state. The API's JSON route still 404s, which is what the client keys on.
4. **`main.py` route order is load-bearing.** If T-007-2 includes its router *after* `mount_single_page_app`, the catch-all swallows `/v/{id}` and the meta tags silently vanish. T-007-2's verify therefore includes a no-JS meta assertion, and its brief spells out the ordering.
5. **Shell injection is string surgery** on the built `index.html` (`<title>` + `</head>`). It assumes the shell keeps those tokens; the fallback shell and the tag assertions keep it honest, and a template engine would replace it later.
6. **`share_views.py` mirrors a 3-line URL rule** instead of importing `job_views._ready_url`, because `job_views.py` is owned by the in-flight `T-005-1` work; T-007-1's brief says to report it if a reviewer prefers extraction.
7. **No browser run.** The real browser pass belongs to T-007-5, whose brief requires a no-JS `curl` proof of the meta tags and accepts skipping the browser with a stated reason.
8. **Spec approval** follows the spec 004/005/006 convention: handing the pack off is the user's approval. If revocable share links must be P0 after all, that is a schema change (a `share_token`) before T-007-1 starts.
9. **Capture:** my tool cannot be wrapped by `scripts/agent-run`, so per AGENTS.md this session's transcript is exported into `.agent-logs/` at commit time.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Spec 007 (Share page) designed + its one new public route published: `GET /api/v1/public/jobs/{job_id}` → `PublicJobResponse` (no auth, no owner/prompt/credits) as a 501 stub, plus the `GET /v/{job_id}` HTML/OG plan; 5 briefs, no migration | `docs/specs/007-share/{spec,design,tasks}.md`, `docs/tasks/T-007-{0..5}/brief.md`, `apps/api/app/schemas/share.py`, `apps/api/app/routers/share.py`, `packages/contracts/openapi.json` | `python3 … openapi paths` → 11 paths incl. `/api/v1/public/jobs/{job_id}` with **no security**; `ls docs/tasks \| grep T-007` → 5 briefs; `scripts/check-standards` → 0 violations; openapi diff **+118/−0** and stable; stub live → 501 without a cookie, 422 for a bad uuid | 2026-09-13 |
