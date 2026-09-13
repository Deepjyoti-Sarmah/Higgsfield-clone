# Design 007: Share page (`/v/{id}`)

**Spec:** `docs/specs/007-share/spec.md` (APPROVED)
**Backend:** `docs/specs/003-generation-core/design.md` (job/asset model, presigned URLs, `require_current_user`); `docs/specs/005-library/design.md` (the job→view builder this reuses).
**Contract:** **ONE** new JSON route — `GET /api/v1/public/jobs/{job_id}` — plus one **HTML** route, `GET /v/{job_id}`, which is deliberately outside the OpenAPI document. Every existing path and schema stays byte-identical. **No migration.**
**Web patterns:** `docs/specs/006-explore/design.md` (shared data in `api/`, copy table, Files table, AC map), `docs/STANDARDS.md` § Styling.

## AC → design → task map
| AC | Design section | Task |
|---|---|---|
| AC-1 Public HTML route | The `/v/{job_id}` HTML route, OG/meta approach | T-007-2 |
| AC-2 Public data route | API contract | T-007-0, T-007-1 |
| AC-3 Succeeded | Component tree, Copy § Result | T-007-4 |
| AC-4 Not ready | Copy § States, `usePublicJob` | T-007-3, T-007-4 |
| AC-5 Failed | Public shape (no `error_message`), Copy § States | T-007-1, T-007-4 |
| AC-6 Not found | `usePublicJob` 404 handling, Copy § States | T-007-3, T-007-4 |
| AC-7 Link preview | OG/meta approach, Copy § Meta | T-007-2 |
| AC-8 Privacy | Public shape | T-007-1, T-007-2 |
| AC-9 Read-only | Flow | T-007-1, T-007-3 |
| AC-10 Accessibility | Accessibility | T-007-4 |
| AC-11 Contract discipline | API contract, Data | T-007-0, T-007-1 |

## API contract (the only contract change)
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| GET | `/api/v1/public/jobs/{job_id}` | path `job_id` (uuid) | **200** `PublicJobResponse` — for **any existing job**, whatever its status | **404** `ErrorResponse` when no such job · **422** malformed uuid |

**Public on purpose:** the route has no `require_current_user` dependency, so `openapi.json` shows it with no security scheme (AC-2). There is no "owner" concept on this route: the same bytes are returned to everyone, which is exactly what makes the share page identical for the owner and a stranger (AC-3).

### `PublicJobResponse` (new; frozen by T-007-0)
| Field | Type | Meaning |
|---|---|---|
| `id` | uuid | the job id, the share key |
| `status` | `"queued" \| "running" \| "succeeded" \| "failed"` | drives the page's state |
| `preset_slug` | string | the effect that made it |
| `preset_name` | string | the page's `h1`; falls back to the slug if the preset row is gone |
| `poster_url` | string \| null | the **ready** generated poster, else null |
| `video_url` | string \| null | the **ready** generated video, else null |
| `created_at` | datetime | generation time |

**Deliberately absent (AC-8):** the owner's id/identity, `prompt` (the user's own words), `credit_cost`, `input_asset_id`, `input_image_url`, `error_message`. A public page must not leak what the user typed, what they paid, or internal failure text — so the client renders its own generic copy for a failed job (AC-5) instead of the job's `error_message`.

**Why not just make `GET /api/v1/jobs/{job_id}` public?** That route's answer is owner-scoped and its shape (`JobResponse`) carries exactly the private fields above. Widening it would change an existing route's security *and* leak `prompt`/credits; a separate, smaller public route keeps the private one private.

## The `/v/{job_id}` HTML route and the OG/meta approach
This is the one genuinely new mechanism in the spec. The SPA cannot provide link previews: `main.py`'s catch-all `@app.get("/{path:path}")` serves the same `index.html` to every path, and crawlers do not run JS.

**Approach (P0, no new dependency, no template engine):**
1. A new router `apps/api/app/routers/share_page.py` declares `GET /v/{job_id}` (`response_class=HTMLResponse`, `include_in_schema=False`) and is included **before** `mount_single_page_app`, because Starlette matches routes in registration order — so it wins over the SPA catch-all for that path only.
2. The handler reads the built shell `index.html` from `settings.static_dir`. If it is missing (API-only environment, or a fresh checkout before `npm build`), it falls back to a minimal built-in HTML document — so the route never 500s and tests do not depend on the web build.
3. It resolves the job through the same public view builder as the JSON route (`services/share_views.py`, from T-007-1) and builds the meta block.
4. It replaces the shell's `<title>…</title>` with the job's title and inserts the meta block immediately before `</head>` — two plain string operations, not a parser.
5. It always answers **200** for `/v/{id}` (even for an unknown id), with generic meta; the client renders the not-found state (AC-6). A 404 status would replace the app shell in some crawlers/browsers and give a worse experience than a rendered state.

**Tags written** (AC-7): `<title>`, `og:title`, `og:description`, `og:type` (`video.other`), `og:site_name`, `og:url`, `og:image` (only when `poster_url` exists), `og:video` (only when `video_url` exists), `twitter:card` (`player` when a video exists, else `summary_large_image`), `twitter:title`, `twitter:image`. Values are HTML-escaped.

**Absolute URLs:** `og:url` comes from `request.base_url` + `v/{job_id}`; `og:image`/`og:video` are the asset URLs from `build_asset_url`, which are already absolute (presigned, or `S3_PUBLIC_BASE_URL`-joined).

## Data
**Nothing changes.** No table, column, index or migration. The public route reads `job` (by primary key — already indexed) plus `preset` (by slug) and `asset` (by id), exactly like `GET /jobs/{id}`. Ledger, claims, leases and the worker are untouched: the share page is read-only, so architecture invariants 1–5 hold.

## Flow
1. A stranger opens `https://<host>/v/<id>`.
2. **Crawler / no-JS:** the API's `/v/{job_id}` handler resolves the job, injects the meta block into the shell and returns HTML — the preview card works with no JS at all (AC-7).
3. **Browser:** the same HTML loads the SPA; `SharePage` calls `GET /api/v1/public/jobs/<id>` through `api/share.ts` with **no** session and **no** guest bootstrap (AC-9).
4. `200` → render by `status`: `succeeded` → video + poster; `queued`/`running` → the "Still generating" state with a Refresh action; `failed` → the generic "didn't finish" state (AC-4, AC-5).
5. `404` → the not-found state (AC-6). Network/other → the error state with Retry.
6. The owner reaching the same URL runs the identical flow — nothing branches on identity (AC-3).

## Component tree
```
SharePage                    (features/share/SharePage.tsx)
├── ShareStates              loading | error | notFound | notReady | failed   (ShareStates.tsx)
│   └── ui/EmptyState + ui/Button/ButtonLink
└── ShareResult              succeeded                                       (ShareResult.tsx)
    └── <video> + meta + "Make your own" link
```
- `SharePage` props: none — it reads `useParams().jobId` and calls `usePublicJob(jobId)`.
- `ShareStates` props: `{ state: "loading" | "error" | "notFound" | "notReady" | "failed"; onRetry: () => void }`.
- `ShareResult` props: `{ job: PublicJob }`.

## Copy (`shareCopy.ts` for the client; the meta strings live server-side)
| Key | Value |
|---|---|
| `page.attribution` | "Made with Higgsfield" |
| `page.cta` | "Make your own" → `/` |
| `page.documentTitle(name)` | `` `${name} · Higgsfield` `` |
| `states.loading.srText` | "Loading this video" |
| `states.error` | title "We couldn't load this video." · body "Check your connection and try again." · action "Retry" |
| `states.notFound` | title "This video doesn't exist or was removed." · body "Check the link, or make your own." · action "Make your own" |
| `states.notReady` | title "Still generating." · body "This video isn't ready yet. Check back in a moment." · action "Refresh" |
| `states.failed` | title "This video didn't finish." · body "Something went wrong while it was being generated." · action "Make your own" |
| `result.download` | "Download" |

**Server-side meta copy** (in `services/share_html.py`, because a crawler never sees the client's):
succeeded → "A 5-second AI-generated video made with the {preset_name} effect on Higgsfield." · not ready → "This video is still being generated on Higgsfield." · failed → "This video isn't available on Higgsfield." · unknown → "Watch AI-generated videos on Higgsfield."

## Files (each ≤ 200 lines; paths relative to the repo root)
| File | New/Edit | Task | Responsibility |
|---|---|---|---|
| `apps/api/app/schemas/share.py` | New | T-007-0 | `PublicJobResponse` (the frozen public shape) |
| `apps/api/app/routers/share.py` | New | T-007-0 → T-007-1 | T-007-0 adds the 501 stub; T-007-1 replaces the body keeping name/signature/responses |
| `apps/api/app/main.py` | Edit | T-007-0, T-007-2 | T-007-0 includes the share router; T-007-2 includes the share-page router **before** the SPA catch-all |
| `packages/contracts/openapi.json` | Edit | T-007-0 | regenerated |
| `apps/api/app/services/share_views.py` | New | T-007-1 | `read_public_job(session, storage, settings, job_id) -> PublicJobView \| None` |
| `apps/api/tests/test_share_api.py` | New | T-007-1 | public read, privacy, states, 404, no session |
| `apps/api/app/routers/share_page.py` | New | T-007-2 | the `GET /v/{job_id}` HTML route (outside OpenAPI) |
| `apps/api/app/services/share_html.py` | New | T-007-2 | meta-tag block + shell injection (escaped, no dependency) |
| `apps/api/tests/test_share_page.py` | New | T-007-2 | meta tags present, escaped, no-JS, unknown id, shell fallback |
| `apps/web/src/api/share.ts` | New | T-007-3 | `PublicJob`, `PublicJobState`, `usePublicJob(jobId)` (no session, no guest bootstrap) |
| `apps/web/src/features/share/shareCopy.ts` | New | T-007-3 | every user-visible share string |
| `apps/web/src/features/share/ShareStates.tsx` | New | T-007-4 | loading / error / notFound / notReady / failed |
| `apps/web/src/features/share/ShareResult.tsx` | New | T-007-4 | the video + attribution + CTA |
| `apps/web/src/features/share/SharePage.tsx` | New | T-007-4 | wire `usePublicJob` → states/result, `document.title` |
| `apps/web/src/App.tsx` | Edit | T-007-5 | `v/:jobId` → `SharePage` (replaces the placeholder `EmptyState`) |
| `docs/tasks/T-007-{0..5}/report.md` | New | each | per-task report |

## Reused
- API: `get_session`, `get_object_storage`, `get_settings`, `find_job` (primary-key read), `find_active_preset`, `find_assets_by_ids`, `build_asset_url` and the `_ready_url` rule — the public view builder mirrors `services/job_views.py` rather than inventing a second URL builder. The existing `ix_job_*` indexes.
- Web: `apiClient` + the generated schema (never a hand-written shape), `ui/Button`, `ui/ButtonLink`, `ui/EmptyState`, `useParams` from react-router, `styles.css` tokens, the eslint limits.
- The static-shell serving already in `main.py` (`mount_single_page_app`) — the new route only *precedes* it; it does not replace it.

## Risks
- **Presigned URLs expire (1h) while a preview card can be cached for days.** `og:image`/`og:video` point at presigned URLs, so a cached card may show a broken image later. Mitigation is a stable public base URL (`S3_PUBLIC_BASE_URL`, already supported) or a permanent media route — both P1; recorded in the spec's out-of-scope.
- **Secret-link semantics.** The share key is the job's UUIDv4, so anyone with the link can view, and there is no revocation in P0 (P1 needs a `share_token`). UUIDv4 is unguessable, which is the accepted P0 bar.
- **Existence disclosure.** The public route 200s for any existing job id and 404s for unknown ones, so a holder of an id learns whether it exists. That is inherent to a share link; the private route's owner-scoped 404 is unchanged.
- **`og:url` trusts the request host.** Behind a proxy, `request.base_url` reflects the forwarded host; if the deployment does not set the forwarded headers, the canonical URL in the card can be wrong. Cosmetic, and Railway sets them.
- **`main.py` route order is load-bearing.** If `share_page.router` were included after `mount_single_page_app`, the SPA catch-all would swallow `/v/{id}` and the meta tags would silently disappear. The task's verify includes a no-JS `curl` assertion precisely to catch that.
- **Shell injection is string surgery.** Replacing `<title>` and inserting before `</head>` assumes the built shell keeps those tokens. The fallback shell and the test that asserts the tags exist keep this honest; a future template engine would replace it.
