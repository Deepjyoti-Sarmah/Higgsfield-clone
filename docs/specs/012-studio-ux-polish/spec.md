# Spec 012, T6: video-target face swap (Pixverse Swap-inspired)

**Status:** SPEC ONLY (no code, no contract edit) · **Priority:** P0 follow-up to spec 011 ·
**Depends on:** spec 011 live (image face swap: `apps/gpu/face_swap.py`, `POST /api/v1/faceswap-jobs`,
Face swap tab, per-clip trim). T1–T5 foundation is summarised in `UX-FIXES-APPLIED.md`.

## Goal

A user picks a **face photo** (source) and a **video** (target, from the rail or an upload) and gets
back a **swapped video**: every detected face in the target is replaced by the source face, while
motion, scene, and the original audio track are preserved byte-for-byte. Pixverse Swap is the UX
reference (pick video → pick face → preview → render), not a code source.

## Non-goals

- No new image-swap behaviour; the 011 image path (`/faceswap-jobs`, 8 credits flat) is reused as-is.
- No multi-face selection UI (all detected target faces get the source face, largest-first like 011).
- No lip-sync, voice change, or audio editing: audio is passed through untouched.
- No avatars, templates, or third-party paid APIs. No contract change to existing routes.
- No videos over the limits below; no non-mp4 targets.

## Acceptance criteria

- **AC-1 Limits enforced at creation:** target video must be mp4 (h264), **≤ 30 s** and **≤ 50 MB**.
  Over-limit or non-mp4 targets are rejected with 422 before any HOLD. Duration/size come from the
  asset metadata recorded at upload completion.
- **AC-2 Keyframe-anchored preview:** before paying for the render, the user sees a still preview:
  frame 0 (fallback: middle frame) of the target swapped with the source face, produced through the
  existing image `POST /faceswap-jobs` path (flat 8 credits, refund-on-failure already built).
- **AC-3 Render preserves motion + audio:** the output video has the same resolution, fps, and
  duration as the target (±1 frame); the audio stream is muxed from the target without re-encoding
  (`-c:a copy` semantics). Verified by ffprobe comparison in tests.
- **AC-4 Per-second credits:** render cost = `ceil(duration_s) × 2` credits (30 s max → 60 max),
  HOLD at creation, SETTLE 0 on success, full RELEASE on failure. Preview cost (8) is separate and
  shown separately. Insufficient balance → 402 with `{detail, balance, required}`, like 011.
- **AC-5 Error cases refund with clear messages** (surfaced verbatim from the GPU 422 detail):
  (a) no face in the source photo; (b) no face found in any checked frame of the target video;
  (c) target longer than 30 s / larger than 50 MB (rejected at creation, no HOLD taken).
  Frames with no detectable face keep the original frame; if over half the sampled frames have no
  face, the job fails with case (b) instead of shipping a mostly-unswapped video.
- **AC-6 Visibility:** the job appears in the rail, on the stage with progress, and on its share page
  as a playable video; it can be added to a sequence like any clip.
- **AC-7 Idempotency + auth:** creation takes an `idempotency_key` (replay returns the same job, no
  second HOLD); cross-user asset ids → 404; `GET` is owner-scoped.

## UX flow

1. **Pick video from rail:** in the studio Face swap tab, a "Video target" toggle switches the target
   well from image to video. The well accepts a rail clip (via a new "Use as swap video" stage action)
   or an mp4 upload (≤ 30 s / ≤ 50 MB, checked client-side before upload completes).
2. **Pick face:** the source well is unchanged (photo upload or rail still).
3. **Preview keyframe:** "Preview" runs the existing image swap on the target's first frame and shows
   the still with its 8-credit cost. The user can swap the face photo and re-preview.
4. **Render:** "Render video (N credits)" shows the per-second cost from the target duration, then
   creates the video job. Progress mirrors the clip job progress UI; failure shows the refund message.
5. **Rail + add-to-sequence:** on success the swapped clip lands in the rail and on the stage with
   "Add to sequence" available, honouring trim like any other clip.
