# Design 012-T6: video-target face swap

Follows the 011 pattern exactly: thin router → creation service (lock → idempotency → limits →
assets → balance → job + step + HOLD → notify) → worker step (claim → lease race → adapter →
upload → SETTLE/RELEASE) → Modal GPU. Nothing in the 011 image path is modified.

## Contract delta (additive only; existing routes untouched)

- `POST /api/v1/video-faceswap-jobs` → 202. Tag `video-faceswap-jobs`.
  Request `VideoFaceSwapJobCreateRequest`: `source_asset_id: UUID` (photo), `target_asset_id: UUID`
  (video), `keyframe_asset_id: UUID | null` (the preview still, informational only),
  `idempotency_key: str` (min 8, max 100). Response `VideoFaceSwapJobCreatedResponse`:
  `id: UUID`, `status: JobStatus`, `credit_cost: int` (the per-second HOLD actually taken).
  Errors: 401 / 402 `{detail, balance, required}` / 404 (asset not found or not owned) /
  422 (over limits, wrong asset kinds, idempotency-key conflict) / 429 (daily limit).
- `GET /api/v1/video-faceswap-jobs/{job_id}` → `VideoFaceSwapJobResponse`: `id`, `status`,
  `credit_cost`, `source_url: str | null`, `target_url: str | null`, `video_url: str | null`
  (only when `succeeded`), `poster_url: str | null`, `duration_ms: int | null`,
  `generated_by: str | null`, `error_message: str | null`, `created_at: datetime`.
- `JobKind` gains `"video_faceswap"`. Library/share treat it as a video kind (playable inline,
  `video_urls` shape), mirroring how T-011-4 mapped `"faceswap"` onto the still shape.
- OpenAPI + `schema.d.ts` regenerated; the diff must contain only the two new paths and the
  widened `JobKind` (lesson from T-011-4: fix the web call sites the widening breaks).

## Worker step (new `swap_face_video` step kind)

1. Load job + assets; fail fast if the source is not a ready image or the target is not a ready
   video whose metadata says mp4 / ≤ 30 s / ≤ 50 MB (re-checked, metadata could have changed).
2. Presigned download URLs for both assets (no local download of the source photo needed beyond
   what the adapter fetches); call the adapter with the lease-renewal race from `adapter_runs`.
3. Adapter returns mp4 bytes + poster bytes; worker verifies with ffprobe
   (duration within 1 frame of target, has exactly one video + at least the target's audio streams).
4. Upload `video-1.mp4` + `poster-1.jpg` under `users/{uid}/jobs/{jid}/`; complete with the video
   success path (SETTLE 0, `job_image`-style row for the poster + video URL row), or
   `complete_step_failure` (RELEASE + verbatim user message) on `GenerationError`.
5. Generation timeout scales with duration: `base_timeout + duration_s × per_second_allowance`
   (concrete numbers are T6b's call; 30 s of 10 fps swap+restore dominates).

## Modal GPU method (extends the 011 endpoint, same app)

- New module `apps/gpu/video_face_swap.py` reusing `face_swap_core` (`require_source_face`,
  `swap_and_restore`) and the same `face-swap-weights` Volume + `FaceSwapper.load` weights.
- Pipeline: fetch target mp4 → ffprobe → decode at max 10 fps (cap 300 frames) → detect faces per
  frame; swap every detected face with the single source face, restore each crop, feather paste-back
  (identical per-frame math to the image path, no new model); frames with no face are copied
  untouched and counted → if unswapped frames exceed half, raise `NoFaceError("No face found in
  the target video")` → re-encode h264 at source size/fps with the target audio muxed via
  `-c:a copy` → return `{video_base64, poster_base64, width, height, fps, duration_s, seconds}`.
- `@modal.method() swap_video(source_url, target_url)` for SDK use plus a bearer-auth
  `@modal.fastapi_endpoint` POST `{source_url, target_url}` mirroring the image endpoint's auth
  and 422-`detail` error shape, so the API adapter stays a thin POST-and-decode like
  `face_swap_adapter.py`. L4 GPU, timeout sized for 300 frames (T6b measures and records it).

## Credit rules (HOLD / SETTLE / RELEASE)

- New `app/domain/video_faceswap_rules.py`: `VIDEO_FACESWAP_CREDITS_PER_SECOND = 2`,
  `VIDEO_FACESWAP_STEP_KIND = "swap_face_video"`, `VIDEO_FACESWAP_BACKEND = "modal-video-faceswap"`,
  `VIDEO_FACESWAP_MAX_SECONDS = 30`, `VIDEO_FACESWAP_MAX_BYTES = 50_000_000`,
  `video_faceswap_cost(duration_s) = ceil(duration_s) × 2`.
- Creation: `lock_user_row` → idempotency replay → `enforce_creation_limits` → asset checks →
  cost from the target asset's `duration_ms` (422 if missing/unparseable) → balance check →
  job + step + `HOLD(-cost)` → notify → commit (same race handling as `faceswap_job_creation.py`).
  Limit rejections (AC-1/AC-5c) happen before the HOLD, so nothing is taken.
- Terminal: success → SETTLE 0 via the video completion path; failure/timeout/lease-lost →
  `complete_step_failure` RELEASEs the full HOLD. The 8-credit keyframe preview is a separate
  image faceswap job with its own HOLD/SETTLE/RELEASE; both charges are shown before submit.

## File ownership (one line each; T6a/T6b/T6c are disjoint)

- T6a contract+data: `migrations/versions/0010_video_faceswap.py` (kind, FKs, checks, downgrade);
  `models/job.py` (two video FK columns + extended checks); `domain/video_faceswap_rules.py` (cost,
  step kind, backend, limits); `schemas/video_faceswap_jobs.py` (request/created/read schemas);
  `schemas/jobs.py` (JobKind + 1 variant); `repositories/video_faceswap_jobs.py` (insert +
  owned-find); `services/video_faceswap_job_creation.py` (one-transaction create);
  `services/video_faceswap_job_views.py` (owned read with presigned URLs);
  `routers/video_faceswap_jobs.py` (POST + GET, status-code mapping); `main.py` (register router);
  `services/job_views.py` + `services/share_views.py` (video shape for the new kind);
  `settings.py` + `.env.example` (`MODAL_VIDEO_FACESWAP_ENDPOINT_URL`); `openapi.json` +
  `schema.d.ts` (regenerated); new `tests/test_video_faceswap_jobs_api.py`.
- T6b gpu+worker: `apps/gpu/video_face_swap.py` (Modal pipeline above);
  `apps/gpu/tests/test_video_faceswap_core.py` (frame-budget, no-face-majority, ffprobe checks);
  `adapters/video_face_swap_adapter.py` (POST `{source_url, target_url}`, 422-detail verbatim,
  base64-mp4 decode); `services/video_faceswap_runs.py` (claim → lease race → verify → upload →
  SETTLE/RELEASE); `worker.py` (dispatch on the new step kind); new
  `tests/test_video_faceswap_step.py`.
- T6c web UI: `api/videoFaceswapJobs.ts` (submit + read outcomes); `api/jobProgress.ts` (poll the
  new GET for the new kind); `features/studio/StudioStage.tsx` + `StageActions.tsx` ("Use as swap
  video" for clips); `features/face-swap/*VideoTarget*` (video well, keyframe preview via the
  existing image submit, per-second cost label, render action); `railItemTitle.ts` ("Video swap"
  title); share/studio video branches (route the new kind through the existing video rendering).
