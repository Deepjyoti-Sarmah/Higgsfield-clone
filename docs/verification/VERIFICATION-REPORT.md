# Live browser verification (T-011) — specs 003–009

**Date:** 2026-09-14
**Target:** https://api-production-8afc.up.railway.app
**Method:** Playwright-core 1.55 + Chromium (headless), viewport 1440x900, deviceScaleFactor 1, a **fresh
signed-out browser context**. Every page below was screenshotted to `docs/verification/<page>.png` and the
result was judged from what the run actually observed (DOM + network responses), not from the spec.
**Deployed commit:** `4b06a17` (T-031 density pass, on top of T-030 own preview media).

> This file **replaces** the earlier draft. That draft claimed hero showcase cards
> (`MOTION DESIGNER`/`EFFECTS STUDIO`/`CINEMATIC CAMERA`), boxed tool cards and "4 4K sample images" that
> were never screenshotted and are not in the current UI. It was written without a browser and is retracted.

## Summary

| # | Page | Result | Evidence |
|---|---|---|---|
| 1 | Explore `/` (signed out) | **PASS** | 12 tiles, first clip `.../previews/dolly-in.mp4`; `explore.png` |
| 2 | Guest session | **PASS** | header pill `Guest · 9ab205` after one click; `explore-guest.png` |
| 3 | Create video `/create/video` | **PASS** | uploaded real JPEG → preset `dolly-in` → job `fa22e5fa-…` → `<video>` rendered; `create-video-ready.png`, `create-video.png` |
| 4 | Library `/library` | **PASS** | `GET /api/v1/jobs` → 200 with 1 item (Dolly In, Ready); `library.png` |
| 5 | Share `/v/{id}` | **PASS** | HTTP 200, `<h1>Dolly In`, 1 `<video>`; server-rendered OG tags; `share.png` |
| 6 | Credits `/credits` | **PASS** | `POST /credits/topup` → "Added 100 credits"; `credits-before.png`, `credits.png` |
| 7 | Create image `/create/image` | **PASS** | prompt → job → `img[alt^="Generated image"]` rendered; `create-image-idle.png`, `create-image.png` |

## 1. Explore, signed out
- `GET /api/v1/presets` returned **12/12 non-null** `preview_url`, all on
  `pub-e14a8ad582a945a7a46dd46e2b138ec2.r2.dev` (probed before and during the run).
- The first tile's clip src was `https://pub-…r2.dev/previews/dolly-in.mp4`; every tile plays its own clip
  (autoplay/muted/loop). Tiles are the whole-link cards from T-031: name + category over a scrim, 20-credits
  chip, "Recreate" on hover/focus.
- Screenshot: `explore.png`.

## 2. Guest session
- Clicking **Continue as guest** once issued the httpOnly cookie and the header switched to `Guest · 9ab205`.
- Screenshot: `explore-guest.png`.

## 3. Create video (a real clip, end to end)
- Uploaded `apps/api/app/adapters/fixtures/preview_sources/source-01.jpg` through the file input; the
  presigned PUT completed (the run observed the `POST /api/v1/uploads/{id}/complete` 200).
- Selected `dolly-in` by clicking its tile (the radio is `sr-only`), then Generate.
- `POST /api/v1/jobs` → job `fa22e5fa-9482-407e-b083-85cef809cd44`; the canvas reached
  **"YOUR VIDEO IS READY"** with the clip playing and Download / Make another / Share actions, balance 40
  (60 grant − 20 hold settled). Screenshots: `create-video-ready.png`, `create-video.png`.

## 4. Library
- After the job settled, `/library` fetched `GET /api/v1/jobs` → **200 with 1 item**
  (`preset_name` "Dolly In", `status` "succeeded", poster + video URLs on the R2 public domain) and rendered
  one row "Dolly In / 13 Sep 2026, 22:33 / Ready". Screenshot: `library.png`.
- Probe note: the first attempt counted `ul li button` while the page was still showing its loading skeleton
  and recorded 0 rows. A focused re-probe of the same flow showed the API returning 1 item and the row
  rendering, so the corrected wait is used here. This is a probe defect, not a product bug.

## 5. Share page and crawler view
- `GET /v/fa22e5fa-…` → **200**, `<h1>` "Dolly In", one `<video>`; screenshot `share.png`.
- No-cookie curl of the same URL returns server-rendered tags **before** JS:
  `<title>Dolly In · Higgsfield</title>`, `og:title`, `og:description`, `og:type=video.other`, `og:url`,
  `og:image` and `og:video` (both on the R2 public domain) and `twitter:card=player`.
- `GET /v/00000000-0000-0000-0000-000000000000` → **200** generic page (existence not leaked).

## 6. Credits
- `/credits` showed the balance card; **Add 100 credits** produced the "Added … credits" confirmation and the
  card updated. Screenshots: `credits-before.png`, `credits.png`.

## 7. Create image
- `/create/image` idle showed the composer (prompt, aspect/quality/count chips) and our own still showcase.
- A prompt was submitted; the run observed `POST /api/v1/image-jobs` and then a rendered
  `img[alt^="Generated image"]`. Screenshots: `create-image-idle.png`, `create-image.png`.

## What this does NOT claim
- Headless Chromium is not a human eye: this is a DOM/network-level pass with screenshots, not a subjective
  design review.
- The video path is the **`local-motion`** ffmpeg backend (the live default). The Modal AI adapter exists but
  `GENERATION_BACKEND` is not switched to it, and that paid path is not exercised here.
- Preview clips are our own ffmpeg-synthesised gradient footage (T-030); the share/create pages were verified
  with those gradients.
- No mobile/responsive viewport, no auth (Google) path, no paid generation.
