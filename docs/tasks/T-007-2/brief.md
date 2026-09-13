# Brief T-007-2: API — serve `/v/{job_id}` HTML with OG meta tags

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/007-share/spec.md` (AC-1, AC-5, AC-7, AC-8)
- Design: `docs/specs/007-share/design.md` § **The `/v/{job_id}` HTML route and the OG/meta approach** (normative) and § **Copy** (the server-side meta strings)
- Existing: `apps/api/app/main.py` (`mount_single_page_app` — the SPA catch-all you must precede), `apps/api/app/settings.py` (`static_dir`), `apps/web/index.html` (the shell with `<title>Higgsfield</title>` and no OG tags)
- Provided by T-007-1: `apps/api/app/services/share_views.py` (`read_public_job`)
- Tests: `apps/api/tests/conftest.py` (`app`, `client`, `guest_client`, `object_storage`)

## Goal
A crawler — or anyone with JS disabled — fetching `GET /v/{job_id}` gets HTML whose `<head>` carries the job's real meta tags, and a browser still gets the SPA shell.

## Allowed files (touch nothing else)
- `apps/api/app/routers/share_page.py` (new)
- `apps/api/app/services/share_html.py` (new)
- `apps/api/app/main.py` (add the router include **before** `mount_single_page_app`)
- `apps/api/tests/test_share_page.py` (new)
- `docs/tasks/T-007-2/report.md`

## Rules
- **Route order is load-bearing.** `create_app()` must `include_router(share_page.router)` **before** `mount_single_page_app(...)`, because Starlette matches in registration order and the catch-all `@app.get("/{path:path}")` would otherwise swallow `/v/{id}` and silently drop the meta tags.
- `GET /v/{job_id}` is declared with `response_class=HTMLResponse` and **`include_in_schema=False`** — it is HTML, not part of the JSON contract, so `openapi.json` must stay **byte-identical**.
- **Always answer 200** (even for an unknown id) with generic meta; the client renders the not-found state (AC-6). Never 500.
- Read the built shell from `settings.static_dir / "index.html"`; if it is absent, fall back to a small built-in HTML document so the route works API-only and tests do not depend on `npm build`.
- Injection is two plain string operations: replace the existing `<title>…</title>`, and insert the meta block immediately before `</head>`. No template engine, no new dependency.
- **Escape every interpolated value** (preset name, urls, description) for HTML attributes. `preset_name` comes from the database, so it must not be able to break out of `content="…"`.
- Tags to write: `<title>` (`"{preset_name} · Higgsfield"`), `og:title`, `og:description` (the per-status strings in design § Copy), `og:type` (`video.other`), `og:site_name` (`Higgsfield`), `og:url` (`request.base_url` + `v/{job_id}`), `og:image` **only when `poster_url` is set**, `og:video` **only when `video_url` is set**, `twitter:card` (`player` with a video, else `summary_large_image`), `twitter:title`, `twitter:image`.
- No private data in the HTML either (AC-8): only the public view's fields and the static copy.
- Keep every file ≤ 200 lines and every function ≤ 40 lines.

## Acceptance checks
- [ ] `GET /v/<a real job id>` with **no cookie** → 200, `content-type: text/html`, and the body contains `<title>` with the preset name plus `og:title`, `og:description`, `og:type`, `og:url`, `twitter:card`
- [ ] a `succeeded` job adds `og:video` and `og:image`; a `queued` job has neither `og:video` nor `<video>`
- [ ] an unknown uuid → 200 with the generic meta (not 500, not 404) and still contains `og:title`
- [ ] a job whose preset name contains `"` and `<` is escaped: the raw characters never appear unescaped inside a content attribute
- [ ] with `static_dir` pointing at a directory with no `index.html`, the route still returns 200 HTML containing the meta tags (fallback shell)
- [ ] `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` → **byte-identical** (the HTML route is not in the schema)
- [ ] ruff, mypy and the full suite are green

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
scripts/check-standards
```

## Out of scope
- The public **JSON** route and its view builder (T-007-1) — import it, do not change it.
- Generated OG images, permanent media URLs, share tokens, caching headers (P1 — see the spec).
- Any `apps/web/**` change: the client page is T-007-4 and the route wiring is T-007-5.

## Report
Write `docs/tasks/T-007-2/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
