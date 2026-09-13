# Spec 004: Create video page

**Status:** DRAFT  ·  **Priority:** P0
**Research refs:** `docs/research/flows/video-create.md` + screenshot `16`; friction notes in `docs/research/product-map.md` § "Better than the original"
**Depends on:** spec 003 contracts (`openapi.json`)

## Problem / why
This is the core loop of the product: image, preset, video. The original page has two upload entry points, preset names that only appear on hover, a crowded control column and promo toasts. Ours should be the fastest path from "I have a photo" to "I have a video".

## User story
As a visitor, I want to drop in a photo, pick a camera move and press Generate, so that I get a shareable video within a minute, and I never have to hunt through the UI or sign up first.

## Acceptance criteria
- **AC-1 Layout:** `/create/video` has a control panel (left on desktop, stacked on top under 768px) and a canvas (right).
  - **Panel order:** Image → Preset → Prompt (optional) → Generate.
  - **Canvas:** shows a "how it works" empty state, or the current job, or the result.
- **AC-2 Image input:** one drop zone that accepts drag & drop, click-to-browse **and** paste from the clipboard.
  - Shows a thumbnail with "Replace".
  - Type/size errors show inline ("PNG, JPG or WebP up to 10 MB").
- **AC-3 Presets:** a grid of preset cards with **names always visible** (no hover needed), category filter chips, and a selected state.
  - `?preset=<slug>` in the URL preselects one (used by Explore "Recreate").
- **AC-4 Generate button:**
  - Shows the real cost ("Generate · 20 credits") and the current balance below it.
  - Disabled until an image and a preset are chosen.
  - Insufficient balance turns it into a "Get credits" link.
- **AC-5 Zero-friction auth:** a signed-out user who presses Generate gets a guest session automatically, and the job starts. One click, no dialog.
- **AC-6 Progress:** after submitting, the canvas shows the input thumbnail, preset name, a live status (Queued → Generating → Done) from SSE, and an elapsed timer. If SSE drops, it falls back to polling every 5s.
- **AC-7 Result:**
  - Autoplaying, muted, looping video with Download, "Make another" (keeps the image, resets the preset) and Share (links to `/v/{id}`, a placeholder until 007).
- **AC-8 Failure:** shows "Generation failed — your 20 credits were refunded" plus Retry.
- **AC-9 Session memory:** the last 6 generations from this session show as a strip under the canvas. Clicking one reopens its result.

## UI states
- **Empty:** onboarding with 3 steps (add image, pick preset, generate) using our own illustrations/preview loops.
- **Loading:** upload progress bar, then job status with timer.
- **Error:**
  - upload error inline
  - 402 → "Get credits"
  - job failed → refund message + Retry
  - network → a toast with Retry
- **Success:** result player + actions.

## Out of scope
- Model picker, references (video/audio), Edit/Motion/Extend tabs, aspect/duration settings (fixed 5s), full library page (005).

## Open questions
- None blocking.
