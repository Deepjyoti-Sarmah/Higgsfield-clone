# Spec 010: Reel & Still (own identity, studio workspace, still → clip → sequence)

**Status:** APPROVED (2026-09-25)  ·  **Priority:** P0 (resubmission, due end of Sat 2026-09-26)
**Research refs:**
- The 8x resubmission email (2026-09-25): "rebuild the frontend with your own layout and visual design; backend real and connected".
- The grilling session of 2026-09-25, whose decisions are captured below.
- Pixovid (`pixovid/`, D-011: not part of this repo) is used **only** for the idea of stitching short clips into longer video. No look, no code.

## Problem / why
The product is a faithful Higgsfield rebuild: its layout, black and #ccff00 palette, Anton type and logo are all Higgsfield's. 8x now wants **our own design choices** on top of our **real backend**. The backend is the strong part:
- the Postgres ledger;
- the worker with claims, leases and the reaper;
- SSE;
- R2;
- Modal FLUX images and LTX video, with an ffmpeg fallback.

So we keep the backend and contract. We give the product its own name, point of view and interface, and add one feature that shows the backend extends cleanly. That feature is **sequences**: stitching clips into a short film.

**Reel & Still** is a small studio for short films. You make stills, animate them into clips, and cut the clips into a sequence, all in one workspace.

## User story
As a guest, I want to make a still, animate it, and cut several clips into one short sequence without leaving one workspace, so that I end up with a finished short film I can share.

## Acceptance criteria (each testable; verify-slice checks exactly these)

### Identity and look
- **AC-1 Brand:** the product is called **Reel & Still** everywhere a user can see: the page title, the header mark, the footer, meta and share pages. The web UI shows no "Higgsfield" text or Higgsfield logo; `grep -ri higgsfield apps/web/src apps/web/index.html` returns nothing.
- **AC-2 Design system:**
  - `DESIGN.md` at the repo root is the single design source. It covers the tokens, type, spacing, components and motion rules.
  - `apps/web/src/styles.css` `@theme` implements it: warm paper background (about `#F6F3EE`), one vermilion accent (about `#C2410C`), Instrument Serif for display, Inter for the UI, and JetBrains Mono for technical values (credits, durations, ids).
  - No component hard-codes a hex value.
- **AC-3 Dark theme:** with `prefers-color-scheme: dark`, the whole app switches to a dark token set defined in the same `@theme` or `@layer base`, with no flash of the light theme on load. Contrast in both themes is WCAG AA for body text.

### Layout
- **AC-4 Studio workspace:** `/studio` is one screen with three parts:
  - a **rail** listing the user's generations, newest first, grouped by day, with a status dot for each;
  - a **stage** showing the selected item or the job in progress;
  - a **composer** with three tabs: **Still · Clip · Sequence**.

  `?item=<job_id>` selects a rail item and survives a reload. At 390px wide the rail becomes a drawer and there is no horizontal page scroll.
- **AC-5 Start page:** `/` is one screen containing:
  - a one-line pitch;
  - the three steps (Still → Clip → Sequence), each illustrated with **real** example media served from our storage (not stock);
  - the motion presets as chips;
  - one primary action, "Open the studio", which goes to `/studio`.
- **AC-6 Redirects:** `/create/video`, `/create/image`, `/library` and `/credits` redirect into `/studio`, with the matching tab (or the credits popover) opened. Old `?job=` links select that item.
- **AC-7 Credits popover:**
  - The balance is always visible in the top bar, in mono type.
  - Clicking it opens a popover with the balance, **"Add demo credits"** (the existing top-up endpoint, labelled as demo, with no payment), and the **last 10 ledger entries** (HOLD / SETTLE / RELEASE / TOPUP, each with its amount, time and job link).
  - A 402 anywhere opens this popover.

### Making things
- **AC-8 Still tab:** prompt, aspect ratio, quality and count, with the live cost. It behaves like spec 009 (create → SSE progress → result), and the result appears in the rail and on the stage.
- **AC-9 Clip tab:** input image (upload, paste or drop), prompt and motion preset, with the live cost. It behaves like spec 004 (upload → create → SSE → result).
- **AC-10 Still → clip:**
  - Each generated still on the stage has an **"Animate this"** action. It switches to the Clip tab with that still as the input, with no download or re-upload.
  - Creating the clip sends the still's `asset_id` as `input_asset_id`, and the API accepts the user's own `ready` `output_image` asset.
  - The API rejects another user's asset (404) and a non-image asset (404), exactly like an unknown id.
- **AC-11 Honest results:** each result shows which backend made it (from the API's `generated_by`/`backend` field). A fallback or placeholder result is captioned as such. The UI never implies a model ran when it didn't.

### Sequences
- **AC-12 Sequence tab:**
  - A horizontal strip of **2–6 slots**. Clips are added from the rail by click or drag ("Add to sequence" on a clip does the same), and they can be reordered and removed.
  - Between each pair of slots is a **transition chip** cycling **Cut / Crossfade / Fade to black**.
  - An optional **music** drop zone.
  - A total duration readout, and **Render · 1 credit**.
  - Render is disabled, with a text reason, when there are fewer than 2 clips.
- **AC-13 Eligibility:**
  - Only the user's own **succeeded video** jobs can be added. Stills, sequences, failed and running jobs can't.
  - Once the first clip is placed, rail clips with a different aspect ratio are greyed out, with the reason shown ("Different shape: 9:16").
  - The API enforces ownership, kind and status as well, returning 404 for a job that isn't yours or doesn't exist and 422 for an ineligible one.
- **AC-14 Create sequence:**
  - `POST /api/v1/sequence-jobs` with clips (each with a transition), an optional `audio_asset_id` and an idempotency key.
  - It returns **202** and writes exactly one `HOLD` of 1 credit in the same transaction.
  - A repeat with the same key returns the same job with no second HOLD.
  - It counts toward the daily job cap.
- **AC-15 Render:**
  - The worker runs a `stitch_video` step under the existing lease.
  - Every clip is normalised to **1280×720 at 24 fps** (letterboxed on black if the aspect ratio differs), and each cut uses its transition (0.5 s crossfade or fade through black; hard cut otherwise).
  - Clip audio is dropped.
  - With music, the track is trimmed to the video's length with a 1 s fade-out and never loops; if it's shorter, the rest is silent.
  - The output is an H.264 mp4 plus a poster frame taken at 1 s.
  - On success: SETTLE. On failure: RELEASE (a refund) and a user-safe `error_message`.
- **AC-16 Progress and result:**
  - The sequence shows queued → running → succeeded/failed over the existing `GET /jobs/{id}/events` SSE stream.
  - On success the stage plays it, with a caption like "3 shots · 14 s".
  - It appears in the rail as a sequence item.
- **AC-17 Music upload:** uploads accept `audio/mpeg`, `audio/mp4` and `audio/wav` up to 10 MB. Other types are rejected with a clear message. Image upload rules are unchanged.

### Sharing, data and access
- **AC-18 Share:** `/v/:id` is Reel & Still's own minimal viewer. It plays clips and sequences (with the shots and length caption) and shows stills, signed out, with no credits or studio UI shown.
- **AC-19 Library contract:** `GET /api/v1/jobs` items include `kind: "sequence"`. Image items expose `images: [{asset_id, url}]` (the existing `image_urls` stays, for compatibility). Sequence items expose their clip count and duration.
- **AC-20 Ledger read:** `GET /api/v1/credits/ledger?limit=10` returns the user's newest ledger entries (`kind`, `amount`, `job_id?`, `created_at`), for the user only.
- **AC-21 Reviewer access:** the per-IP guest cap is raised from 5 to 30 per day (`GUEST_PER_IP_DAILY`). The per-user daily job cap and the paid budget guard are unchanged.
- **AC-22 Contract discipline:**
  - `packages/contracts/openapi.json` is regenerated and CI's sync check passes.
  - The only contract changes are the additions named in AC-10, AC-14, AC-17, AC-19 and AC-20. Every existing path keeps its behaviour for existing clients.
  - Data changes are **one additive migration** (`0007`).
- **AC-23 Stale decision fixed:** a new decision in `docs/DECISIONS.md` supersedes D-014, recording that images are real (FLUX.1-schnell on Modal) with a labelled placeholder fallback.

## UI states (every one must be designed, in both themes)
- **Empty:**
  - A fresh guest's rail shows a short "Nothing here yet. Start with a still or drop an image." with the Still tab focused.
  - An empty Sequence strip shows two dashed slots reading "Add a clip from the rail".
- **Loading:**
  - The rail uses skeleton rows (`aria-busy`).
  - The composer options load with a skeleton, and Generate/Render stay disabled.
  - The stage shows the SSE phase with elapsed time and a polite live region.
- **Error:**
  - Options or rail load failures get Retry.
  - Upload type or size errors appear inline.
  - A failed job shows its user-safe message and "credits refunded".
  - A 402 opens the credits popover.
  - A 429 (daily cap) states the limit and when it resets.
- **Success:** the result is on the stage with its actions:
  - still: Animate this · Download · Share;
  - clip: Add to sequence · Download · Share;
  - sequence: Download · Share.

  The backend caption is shown (AC-11).

## Out of scope
- Any change to how existing video and image generation, the ledger rules or the worker claim/lease work. Sequences only **add** a step kind.
- Face swap, avatars, templates, a timeline editor with trimming (Pixovid ideas we're not building).
- Per-clip trimming, speed changes, text overlays, more than 6 clips, nested sequences, looping or mixing audio.
- Real payments; accounts beyond guest sessions.
- The 1-minute intro video and walkthrough recording (done by the user).

## Open questions
- None blocking. Credits: the sequence costs 1 credit (clips cost 20, stills 10–15 each), and that's deliberate. Stitching uses no GPU, and the charge exists to show the ledger on a second job kind.
