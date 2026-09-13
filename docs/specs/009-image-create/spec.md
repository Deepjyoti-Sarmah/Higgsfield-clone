# Spec 009: Create image (text → image)

**Status:** DONE  ·  **Priority:** P1
**Research refs:** `docs/research/product-map.md` row "Image create: prompt + aspect/quality/count → images" (**P1**, "Second creation mode. Images can also be generated and fed into Video create"); `docs/research/flows/image-create.md` (screenshot `15`, empty state only — generating/results were never captured); `docs/DECISIONS.md` D-002 (image model = LLaDA-Image Turbo on Modal, **licence unverified**), D-012 (Image create is P1); `docs/specs/003-generation-core/design.md` (the job/asset/ledger core this reuses); `docs/specs/004-create-video/design.md` (the page conventions)

## Problem / why
The product has two creation modes and ships one. `/create/image` is a literal placeholder (`App.tsx` → `<Placeholder title="Create image" />`) while the nav item has been there since the shell. The core machinery an image mode needs already exists and is generic where it matters — one `job` with a credit HOLD, a claimable `job_step` with a lease and a reaper, `SETTLE`/`RELEASE`, and a `GET /jobs/{id}/events` SSE stream — but the *shape* is video-only: `job.preset_slug` and `job.input_asset_id` are `NOT NULL`, `asset.kind` has no `output_image`, and the worker's success path writes exactly `video.mp4 + poster.jpg`.

This spec adds the second mode by **extending** that core (one additive migration, one new asset kind, one new step kind, one new adapter) rather than duplicating it.

**Backend reality, stated honestly.** There is **no image model adapter today**, and the model D-002 names (LLaDA-Image Turbo on Modal) is **not runnable here**: no Modal deployment, R2 credentials are blocked (STATUS BROKEN), and its licence is unverified. So this spec does **not** promise a real model. P1 ships the whole slice against a **placeholder image backend** (`local-motion` and `mock` both write a deterministic PNG at the requested aspect ratio; `modal`/`openrouter` fail with "image generation is not configured"), the API returns the backend name, and the page captions a placeholder result as such (AC-10). Swapping in the real model later is one adapter + one `generate_image` implementation — the port already exists. Real text→image is **P2**.

## User story
As a guest, I want to describe an image, choose its shape/quality/count, and see the credit cost before I generate, so that I can make still images the same way I make videos — and later feed one into Video create.

## Acceptance criteria (each testable; verify-slice checks exactly these)
- **AC-1 Route:** `/create/image` renders the Create image page inside `AppShell`; the nav item already points there, so no nav change is needed.
- **AC-2 Signed out:** with no cookie, the page first gets a guest session automatically (the spec-004 runner, `api/guestSession.ts`) and then works; there is no login wall. A 401 is retried exactly once after the guest session is ensured.
- **AC-3 Prompt:** a required 1–500 character prompt; Generate is disabled (with a text reason) until it is non-empty.
- **AC-4 Settings + honest cost:** aspect ratio (`1:1`,`4:5`,`3:2`,`16:9`,`9:16`), quality (`standard`,`high`) and count (1–4) are chosen from values and unit costs returned by `GET /api/v1/image-options`; the Generate button shows the live cost (`Generate · N credits`) **before** generating, and it changes with quality/count. No strikethrough "was/now" pricing.
- **AC-5 Create:** Generate → `POST /api/v1/image-jobs` with a fresh idempotency key → **202** `{id, status, credit_cost, image_count}`; exactly one `HOLD` of `credit_cost` is written in the same transaction and the balance drops immediately. A repeat with the same key returns the same job and never holds twice.
- **AC-6 Progress:** the page shows queued → running → succeeded/failed using the existing `GET /api/v1/jobs/{job_id}/events` SSE stream with the 5 s poll fallback and the reconnect ladder — no second watcher implementation (the spec-004 watcher moves to `api/`).
- **AC-7 Result:** on success the page renders exactly `count` images from `GET /api/v1/image-jobs/{job_id}` in a grid, each with a descriptive `alt` and a Download link. The images are the stored assets; the client never fabricates or resizes them.
- **AC-8 Failure + refund:** a failed job shows the generic failure copy and the credits are refunded (`RELEASE`), exactly like video; the job's internal error text is shown only as the contract's user-safe `error_message`.
- **AC-9 Out of credits:** a **402** shows the returned `balance`/`required` in text plus a "Get credits" link to `/credits`; no job is created and no HOLD is written.
- **AC-10 Backend honesty:** `GET /image-jobs/{id}` returns the `backend` that produced the images. When it is a placeholder backend the page shows a visible "demo placeholder" caption; the design, this spec and the README state that no real image model runs yet. `modal`/`openrouter` fail with a clear "not configured" message and a refund rather than pretending to generate.
- **AC-11 Library discipline:** image jobs **do not** appear in the video Library (`GET /api/v1/jobs` stays video-only) and `GET /api/v1/jobs/{job_id}` **404s** for an image job; `GET /api/v1/image-jobs/{job_id}` is the image read. (Unifying the Library is P2.)
- **AC-12 Contract + data discipline:** every pre-existing path and schema in `packages/contracts/openapi.json` stays byte-identical; the only additions are `GET /api/v1/image-options`, `POST /api/v1/image-jobs`, `GET /api/v1/image-jobs/{job_id}` and the image schemas. Data changes are **one additive migration** (`0004`): a nullable-per-kind `job.kind`/params, the `output_image` asset kind and the `job_image` child table. No existing column is dropped and no existing route's behaviour changes for video jobs.

## UI states (every one must be designed)
- **Empty:** no prompt yet — the composer is ready, Generate disabled with a text reason.
- **Options loading:** the settings row is an `aria-busy="true"` skeleton and Generate stays disabled.
- **Options error:** "We couldn't load the image options." + Retry (the page is unusable without valid values, so this is a blocking error state).
- **Submitting:** Generate disabled, "Starting...".
- **Queued / generating:** the SSE phase with a polite live-region announcement and elapsed-safe copy.
- **Success:** the images grid (`count` images) + per-image Download + "Make another".
- **Failed:** generic failure copy, no images, credits-refunded line.
- **Out of credits:** the 402 balance/required line + "Get credits" → `/credits`.

## Out of scope
- **A real image model (P2).** LLaDA-Image Turbo on Modal is blocked on licence + GPU + R2; `modal`/`openrouter` keep failing as they already do for video (D-002/D-003). P1 is the placeholder backend only.
- **Feeding an image into Video create (P2).** Would require Video create's upload to accept an `output_image` asset id; the product-map reason is recorded for P2.
- **Images in the Library / Share / the session-history strip (P2).** `GET /jobs`, `GET /jobs/{id}` and the Library schema stay video-only (AC-11); image results live on `/create/image` for this slice.
- Image detail view, upscale, inpaint, edit (product-map: P2).
- Reference-image input, negative prompt, seed, style presets, a model picker, watermark/NSFW handling.
- Count > 4, per-image pricing breakdown, batch pricing discounts.
- Face swap (D-004, separate P1 item) and text→video-through-images chaining.
- Any change to the presets, uploads, credits, top-up or share contracts.

## Open questions
- **Real model + licence.** D-002 flags LLaDA-Image Turbo's licence as unverified. Before P2, verify it or pick an alternative; the adapter port (`ImageModelAdapter`) is designed so that decision does not touch the API, the worker branch, or the page.
- **Cost formula.** This spec prices an image at 10 credits (standard) / 15 (high) per image, so 1–4 images cost 10–60 — the same "honest, integer, preset-free" style as video's flat 20. Aspect ratio does not change the cost. If a future model's cost is token/size dependent, `domain/image_rules.image_credit_cost` is the single place to change.
- **Library unification (P2).** Whether an image job becomes a Library row (thumbnail = first image) and how it deep-links is deliberately deferred; AC-11 keeps the P0 Library contract intact until then.
