# Spec 007: Share page (`/v/{id}`)

**Status:** DONE  ·  **Priority:** P0
**Research refs:** `docs/research/product-map.md` row 23 ("Community projects / profiles / likes → P2 … Share pages (`/v/{id}`) cover the growth loop") and gap 6 of § "Not yet observed" ("Share / public view of a generation: the page someone opens from a link"); `docs/research/flows/video-create.md` (16, result + History); `docs/specs/003-generation-core/design.md` (job/asset model, presigned URLs); `docs/specs/004-create-video/design.md` (result view)

## Problem / why
A finished video is only reachable by its owner, inside Create video or the Library. There is **no public link**, so the growth loop the product map relies on does not exist. Two things block it today:

1. `GET /api/v1/jobs/{job_id}` is **owner-only** — it 404s for everyone else — so there is no public way to read a generation.
2. The web app is a **client-rendered SPA**: `main.py`'s catch-all serves the same `index.html` for every path. A stranger's browser would render fine once JS runs, but a chat/social crawler (which does not run JS) sees an empty shell with no preview.

So this spec adds one public JSON route and serves **per-job HTML** for `/v/{id}` with real `<meta>` tags.

## User story
As a visitor who was sent a link, I want to open `/v/{id}` and watch the video — with a useful preview card in the app I received the link in — so that I can see what was made and make my own.

## Acceptance criteria (each one testable; verify-slice checks exactly these)
- **AC-1 Public HTML route:** `GET /v/{job_id}` returns HTML **with no cookie and no session**, and its `<head>` carries per-job `<meta>` tags. It is served by the API, not by the generic SPA fallback.
- **AC-2 Public data route:** `GET /api/v1/public/jobs/{job_id}` is unauthenticated (no cookie required, `security: []` in `openapi.json`) and returns `PublicJobResponse`.
- **AC-3 Succeeded:** `/v/{id}` shows the video (`controls`, `muted`, `playsInline`, `poster` when a poster exists), the preset name as the page's only `h1`, a "Made with Higgsfield" attribution, and a "Make your own" link. The owner opening their own link sees the identical page.
- **AC-4 Not ready:** a `queued` or `running` job shows the "Still generating" state: no `<video>` element at all, no error styling, and a "Refresh" action that re-fetches.
- **AC-5 Failed:** a `failed` job shows the "didn't finish" state with generic copy. The job's internal `error_message` is **never** shown (it is not in the public schema).
- **AC-6 Not found:** an unknown id → the API answers 404 and the page shows "This video doesn't exist or was removed." plus a "Make your own" link. The page must not crash or render an empty shell.
- **AC-7 Link preview:** `curl -s http://<host>/v/<id>` (no JS, no cookie) returns HTML whose `<head>` contains `<title>` naming the preset, plus `og:title`, `og:description`, `og:type`, `og:url`, `twitter:card`, and `og:image` whenever a poster exists — and `og:video` for a succeeded job.
- **AC-8 Privacy:** neither the public JSON nor the HTML exposes the owner's identity or id, the `prompt`, `credit_cost`, any asset id, the input image, or the internal error text.
- **AC-9 Read-only:** opening a share link never creates a session, never touches credits, and never mutates state.
- **AC-10 Accessibility:** exactly one `h1` (the preset name); the video is `muted` + `playsInline` with visible controls; every status is text, never colour-only; the CTA is a real link; the loading region is `aria-busy="true"`.
- **AC-11 Contract discipline:** every pre-existing path and schema stays byte-identical. The only additions are `GET /api/v1/public/jobs/{job_id}` and `PublicJobResponse`. `/v/{job_id}` is deliberately **not** in the OpenAPI document — it returns HTML, not JSON, so it is declared `include_in_schema=False`.

## UI states (every one must be designed)
- **Empty (not found):** title "This video doesn't exist or was removed." · body "Check the link, or make your own." · action "Make your own" → `/`.
- **Loading:** `aria-busy="true"` region with a video-shaped skeleton and text lines, so the swap does not shift the page.
- **Error (network or non-404 failure):** title "We couldn't load this video." · body "Check your connection and try again." · action "Retry".
- **Success:** the video + preset name + attribution + "Make your own". Two designed sub-states: **not ready** ("Still generating." + Refresh) and **failed** ("This video didn't finish.").

## Out of scope
- **Owner controls on the share page (P1):** delete, "stop sharing", visibility toggle, or a revocable share token. P0 keys the page by the job id (an unguessable UUIDv4), so a link is shareable-but-secret.
- **Social layer (P2, product-map row 23):** likes, comments, view counts, creator profiles, a community feed.
- **Generated OG images / thumbnail compositing (P1):** the poster is used when it exists; when it does not, the card falls back to text-only.
- **Permanent media URLs / CDN (P1):** asset URLs stay presigned (they expire); a crawler that caches a card may hold an expired image. See the design's risks.
- Copy-link button, QR code, analytics, embeds, `?autoplay` variants.
- The Library's private result panel (spec 005) remains owner-only and is not changed here.

## Open questions
- None blocking. Whether share links should later be revocable is a real product question, deliberately deferred to P1 (it needs a `share_token` column and a migration).
