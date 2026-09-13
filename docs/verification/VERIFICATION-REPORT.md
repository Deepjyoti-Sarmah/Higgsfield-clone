# Functional Slice Verification Report (Specs 003 – 009)

**Date:** 2026-09-14  
**Target Host:** `https://api-production-8afc.up.railway.app`  

---

## 1. Signed-Out Explore Landing Page (Spec 006)
- [x] **Route `/`**: Serves index HTML with HTTP 200 signed out.
- [x] **Brand Header**: Renders Higgsfield SVG logo icon, navigation links (`Explore`, `Create video`, `Create image`, `Library`, `Credits`), and guest session pill (`Guest · <hash>`).
- [x] **Explore Hero**: Displays 3 showcase video cards (`MOTION DESIGNER`, `EFFECTS STUDIO`, `CINEMATIC CAMERA`) with live looping MP4 backgrounds.
- [x] **Tool Cards**: 5 navigation tool cards (`Explore`, `Create video`, `Create image`, `Library`, `Credits`) render cleanly with icons, description tags, and hover state transitions.
- [x] **Preset Gallery**: 12 motion presets grouped into `Camera`, `Cinematic`, and `Dynamic` categories. Every tile plays a looping video preview on hover with credit cost pill (`20 CREDITS`) and "✦ RECREATE" button.

---

## 2. One-Click Guest Auth & Video Creation (Specs 002, 003, 004)
- [x] **Guest Cookie**: Automatic HTTP-only JWT guest cookie issued on first interaction (`POST /api/v1/auth/guest` -> 60 credits GRANT).
- [x] **R2 Image Upload**: Drag/drop or file select generates presigned PUT URL (`POST /api/v1/uploads`), uploads file directly to Cloudflare R2, and marks asset ready (`POST /api/v1/uploads/{id}/complete`).
- [x] **Idempotent Job Creation**: `POST /api/v1/jobs` holds 20 credits, creates step queue, emits `202 Accepted` with idempotency key.
- [x] **Live Progress & Worker Dispatch**: SSE endpoint (`GET /api/v1/jobs/{id}/events`) streams `queued -> running -> succeeded`. Worker claims step via `FOR UPDATE SKIP LOCKED`, generates 720p H.264 MP4 + poster into R2, and settles credit ledger (balance drops 60 -> 40).
- [x] **Result Actions**: Playback video, download MP4, "Make another", "Share".

---

## 3. Create Image Page (Spec 009)
- [x] **Route `/create/image`**: Renders prompt input, aspect ratio chips (`Square`, `Portrait`, `Landscape`, `Wide`, `Vertical`), quality selector (`Standard`, `High`), and count chips (`1`, `2`, `3`, `4`).
- [x] **Idle Stage**: Displays `ImageIdleShowcase` with 4 sample 4K generated images when no job is active.
- [x] **Image Job Generation**: `POST /api/v1/image-jobs` validates parameters, holds credits (10/15 per image), generates PNG asset, and displays result grid.

---

## 4. Library Page (Spec 005)
- [x] **Route `/library`**: `GET /api/v1/jobs` returns user's historical generations newest-first with thumbnail posters, preset labels, and relative timestamps (`FormatCreatedAt`).
- [x] **Result Panel**: Selecting any library item plays the video inline with result action buttons.

---

## 5. Credits & Fake Top-Up (Spec 008)
- [x] **Route `/credits`**: Displays current ledger balance card (`SUM(ledger)`).
- [x] **Fake Top-Up**: `POST /api/v1/credits/topup` inserts `TOPUP` (+100 credits) ledger row, updating real-time balance.

---

## 6. Public Share Page & OpenGraph Tags (Spec 007)
- [x] **Route `/v/{job_id}`**: `GET /v/{job_id}` returns server-rendered HTML with `<title>`, `og:title`, `og:video`, `og:image`, and `twitter:card` meta tags before JS hydration (verified via no-cookie `curl` probe).
- [x] **Public API**: `GET /api/v1/public/jobs/{job_id}` returns public-safe job payload without sensitive user or credit metadata.
