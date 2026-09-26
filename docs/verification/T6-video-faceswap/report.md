# T6d — video-target face swap end-to-end verify (MOCK backend only)

Date: 2026-09-26 UTC. No product code changed; no commit.
Scope: `GENERATION_BACKEND=mock`, local compose DB (postgres:17, Up 20h).
Paid Modal probe NOT run (BLOCKED — no spend approved). One paid render max
reserved for later live slice verification.

## Verify outputs (pasted)

API (mock backend), full suite:

```
$ GENERATION_BACKEND=mock uv --directory apps/api run pytest -q
297 passed, 3 warnings in 88.24s (0:01:28)
```

Video-faceswap slice alone:

```
$ GENERATION_BACKEND=mock uv --directory apps/api run pytest -q \
    tests/test_video_faceswap_jobs_api.py \
    tests/test_video_faceswap_target_job_api.py \
    tests/test_video_faceswap_step.py
15 passed in 3.71s
```

GPU core math (no paid call):

```
$ uv run --with numpy --with pytest pytest apps/gpu/tests/test_video_faceswap_core.py
8 passed in 0.07s
```

Web:

```
$ npm --prefix apps/web run typecheck   # tsc -b -> exit 0
$ npm --prefix apps/web run build
dist/assets/index-D2f9jZu9.js   393.33 kB | gzip 118.01 kB   built in 323ms
$ npm --prefix apps/web run test
Test Files  24 passed (24) / Tests  120 passed (120)
```

Standards:

```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Live mock-flow probe (throwaway pytest, deleted after run)

Guest (grant 60) -> upload photo + 5 s mp4 producer job -> render via
`target_job_id` with the same `idempotency_key` replayed:

```
T6D guest grant balance=60
T6D render cost for 5000ms: ceil(5)*2 = 10
T6D created job=290b7ff8-... status=queued credit_cost=10
T6D ledger after create: [('HOLD', -10)]
T6D balance after HOLD: 50
T6D idempotent replay same id=True ledger still: [('HOLD', -10)]
T6D after run: status=succeeded generated_by=modal-video-faceswap
  duration_ms=1000 video_url=set
T6D ledger after settle: [('HOLD', -10), ('SETTLE', 0)]
T6D balance after SETTLE: 50
T6D >30s target: HTTP 422 detail=target over duration limit: 0d761399-...
T6D balance unchanged after 422: 50
T6D faceless: status=failed
  error_message='No face found in over half of the video frames'
T6D faceless ledger: [('HOLD', -10), ('RELEASE', 10)]
T6D balance after refund: 50
1 passed in 1.30s
```

Swap payload fed to the step was a locally ffmpeg-built clip
(320x240 h264 10 fps + aac, 1.000 s, 17683 B):

```json
{"streams": [
  {"codec_name": "h264", "codec_type": "video",
   "width": 320, "height": 240, "avg_frame_rate": "10/1"},
  {"codec_name": "aac", "codec_type": "audio", "avg_frame_rate": "0/0"}],
 "format": {"duration": "1.000000", "size": "17683"}}
```

The worker's `verify_video_output` ffprobe check passed on it and recorded
`duration_ms=1000`; a poster was extracted and both artifacts uploaded.

## What the mock adapter returns (documented, not assumed)

- `MockModelAdapter` (`apps/api/app/adapters/mock_model_adapter.py`) only
  implements `generate_video`: copies `fixtures/mock-video.mp4`
  (64x64 h264, 24 fps, 1.000 s, 2205 B, **video-only, no audio stream**)
  + `mock-poster.jpg`, reports 64x64 / 1000 ms. It does NOT serve
  face-swap steps.
- Both swap adapters (`FaceSwapAdapter`, `VideoFaceSwapAdapter`) are
  Modal-only: with no endpoint configured they raise
  `BackendNotConfiguredError`. So under `GENERATION_BACKEND=mock` the
  GPU byte-transform itself is exercised via the fake-adapter step tests
  above (real ffprobe verify + real ledger SETTLE/RELEASE), and the real
  Modal transform + audio `-c:a copy` mux (`apps/gpu/video_face_swap.py:57`)
  await the one reserved paid render.
- `verify_video_output` checks the video stream + duration only; audio
  passthrough is asserted in the GPU core tests (8 passed), not in mock.

## AC table

| AC | Check | Result |
|---|---|---|
| AC-1 Limits at creation | mp4/h264, ≤30 s, ≤50 MB; `too_long`/`too_big`/`webm`/`unknown-duration` targets -> 422 each, balance stays 60 (`test_over_limit_targets_rejected_without_hold`); live probe: 31 s target -> 422 `target over duration limit`, balance unchanged | PASS |
| AC-2 Keyframe preview | Preview rides the existing image `POST /faceswap-jobs` path at flat `FACESWAP_CREDIT_COST = 8` (unchanged code); render accepts `keyframe_asset_id` (`test_keyframe_asset_id_is_accepted` -> 202). GPU execution of the preview itself needs the paid endpoint (see BLOCKED) | PASS (wiring + contract; pixels pending paid render) |
| AC-3 Motion + audio | Worker ffprobe-verifies output before upload; probe clip 320x240/10fps/1.000s verified, `duration_ms=1000` recorded; GPU mux uses `-c:a copy -shortest` (`apps/gpu/video_face_swap.py:57`); mock fixture is video-only so audio-copy is proven only in GPU core tests | PASS (mock level; byte-compare pending paid render) |
| AC-4 Per-second credits | `ceil(5000ms)=5s -> 10` credits; ledger `HOLD -10` then `SETTLE 0`, balance 60->50->50 (probe excerpt above) | PASS |
| AC-5 Error refunds | (a/b) GPU 422 detail surfaced verbatim: `error_message='No face found in over half of the video frames'`, ledger `HOLD -10, RELEASE +10`, balance restored (`test_faceless_video_fails_and_refunds_verbatim` + probe); (c) >30 s -> 422 with no HOLD row. Faceless-*source*-photo pixels need the paid endpoint | PASS (mock level) |
| AC-6 Visibility | `video_faceswap` kind wired in rail (`railItemTitle.ts`, `RailKindBadge`), stage (`StudioStage.tsx`, `StageActions.tsx` incl. add-to-sequence), share (`ShareResult`, `shareCopy`), progress (`jobProgress.ts`); web typecheck + build + 120 vitest green. Playback of a real swapped video pending paid render | PASS (build level; live playback BLOCKED) |
| AC-7 Idempotency + auth | Replay with same key returns same id, still one HOLD (probe); cross-user target asset/job -> 404 (`test_foreign_target_is_404`, `test_foreign_target_job_is_404`); cross-type key reuse -> 422; owner read 200 with `video_url`/`poster_url` null while queued, stranger read 404 | PASS |

Paid Modal probe (one `swap_video.remote` + one keyframe `swap.remote`):
BLOCKED — no spend approved. Reserved for the later live slice (record cost then).

## RESULT: PASS (mock backend; paid render explicitly out of scope and BLOCKED)
