# Spec 003: Generation core (presets, uploads, jobs, credits, worker, live progress)

**Status:** DRAFT  ·  **Priority:** P0
**Research refs:** `docs/research/flows/video-create.md` (presets, cost on Generate, History); `docs/architecture/architecture.md` invariants 1–5; D-001, D-002, D-003, D-006

## Problem / why
Every creation feature (video now, image and face swap later) needs the same engine:
- take inputs
- charge credits safely
- queue work
- run a backend
- store the output
- stream progress

Building it once, behind stable API contracts, lets the UI specs (004+) be built in parallel by other agents.

**Product call:** the default backend is **`local-motion`**. ffmpeg applies a real camera move (dolly in/out, pan, orbit-style push, handheld shake…) to the user's own image, per preset. The whole product then works end to end at $0 with no GPU. `modal` (LTX-2.5) and `openrouter` slot in behind the same adapter once credentials exist.

## User story
As a user, I want to pick a motion preset for my image and get a video back with visible progress, so that I'm never charged for a generation that fails.

## Acceptance criteria
- **AC-1 Presets:** `GET /api/v1/presets` returns ≥12 active presets.
  - Fields: `slug`, `name`, `description`, `category`, `credit_cost`, `preview_url` (nullable).
  - It works signed out.
- **AC-2 Uploads:**
  - `POST /api/v1/uploads` `{content_type, byte_size}` returns `{asset_id, upload_url}` (a presigned PUT) for jpeg/png/webp ≤ 10 MB.
  - `POST /api/v1/uploads/{asset_id}/complete` checks that the object exists and marks the asset `ready`.
  - Other types or sizes return 422.
- **AC-3 Create job:** `POST /api/v1/jobs` `{preset_slug, input_asset_id, prompt?, idempotency_key}` returns **202** `{id, status:"queued", credit_cost}`.
  - One transaction: HOLD ledger row (−cost), job + step insert, `NOTIFY job_events`.
  - Repeating the same `idempotency_key` returns the same job and creates no second hold.
  - Insufficient balance returns **402** `{balance, required}`.
- **AC-4 Worker:**
  - Claims one queued step with `FOR UPDATE SKIP LOCKED` and a 5-minute lease, and runs the backend chosen by `GENERATION_BACKEND`.
  - **On success:** stores the output mp4 (+ a poster jpg) as assets, SETTLEs the hold, sets job `succeeded`.
  - **On failure:** RELEASEs the hold (+cost), sets job `failed` with a user-safe `error_message`.
  - Two workers never run the same step.
- **AC-5 Reaper:** a step whose lease expired is re-queued once, then failed and released.
- **AC-6 Progress:**
  - `GET /api/v1/jobs/{id}/events` is an SSE stream.
  - It emits `status` events within 1s of each change (queued → running → succeeded|failed), plus `: ping` every 20s.
  - `GET /api/v1/jobs/{id}` returns the same data for polling.
  - Only the job's owner can read it (404 for anyone else).
- **AC-7 Credits:**
  - `GET /api/v1/credits` returns `{balance}` = `SUM(ledger)`.
  - A new guest gets a one-time GRANT of **60** credits. A 5s video preset costs **20**.
- **AC-8 Backends:**
  - `local-motion` produces a real 5s mp4 (≤720p, h264, faststart) from the input image using the preset's motion recipe.
  - `mock` (tests) completes instantly with a tiny fixture.
  - `modal` and `openrouter` adapter classes exist behind the Protocol and fail clearly with "backend not configured" until credentials are set.
- **AC-9 Tests:** double-claim, idempotency, insufficient credits, failure release, lease expiry, SSE status sequence, owner-only access.

## UI states
- None in this spec: it's API only. Spec 004 consumes it.

## Out of scope
- UI (004), library listing (005), share page (007), top-up (008), image/face-swap job types (P1), real Modal/OpenRouter calls (placeholder).

## Open questions
- None blocking. Credit numbers (60 grant / 20 per video) can be tuned in one config place.
