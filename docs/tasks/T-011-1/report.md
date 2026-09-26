# Report T-011-1

**Agent:** sonnet-5@claude-code · **Role:** implementer (GPU) · **Result:** DONE

## Files changed
- `apps/gpu/fit_input.py` (new): pure Pillow `fit_to_output(image) -> (image, width, height)`. Picks landscape 960x544 / portrait 544x960 / square 704x704 from aspect ratio (thresholds 1.2 and 0.83), center-crops to that aspect, then LANCZOS-resizes. All dimensions are multiples of 32.
- `apps/gpu/ltx_video.py` (new): `@app.cls(gpu="H100", scaledown_window=300, ...)` with `@modal.enter()` loading `LTX2ImageToVideoPipeline` once per container, and a `@modal.fastapi_endpoint(method="POST")` method `generate_clip_endpoint` with the same auth, request and response shape as `ltx_spike.py`'s endpoint. Width/height come from `fit_to_output`; empty/missing prompt returns 422. `DEFAULT_NEGATIVE_PROMPT`, `DISTILLED_SIGMA_VALUES` and `CLIP_FRAMES`/`CLIP_FPS` kept as in the spike.
- `apps/gpu/tests/test_fit_input.py` (new): landscape, portrait, square, tiny-image and multiple-of-32 checks.
- `docs/tasks/T-011-1/report.md` (this file).
- `docs/verification/T-011-1/frames.png` (new): 3-frame tile (frame 0 / 60 / last) from the live render.

## Reused
- Copied the working request/response/auth/pipeline-call shape from `apps/gpu/ltx_spike.py`'s `generate_clip_endpoint`, per the brief. `ltx_spike.py` itself is untouched (verified with `git status`/`git diff --stat`).
- Kept the same `ltx-weights` Modal volume and `huggingface`/`modal-auth` secrets.

## Verify
```
apps/api/.venv/bin/python -m pytest apps/gpu/tests -q && apps/api/.venv/bin/python -m py_compile apps/gpu/ltx_video.py apps/gpu/fit_input.py
```
Pillow was initially missing from `apps/api/.venv` (a symlink shared with the main checkout). First checked with `uv run --with pillow --with pytest python -m pytest apps/gpu/tests -q` (5 passed), then installed Pillow into the shared venv itself with `uv pip install --python apps/api/.venv/bin/python pillow` so the brief's literal verify command (and `scripts/task verify`) runs unmodified. `scripts/task verify T-011-1` now ends `RESULT: PASS`; see `verify.log`.

## Standards check
```
check-standards: ok (0 violations)
```
File sizes: `ltx_video.py` 140 lines, `fit_input.py` 39 lines, `tests/test_fit_input.py` 42 lines — all well under 200.

## Deploy and live check
Deployed with `modal deploy apps/gpu/ltx_video.py`:
- **Endpoint URL:** `https://deepjyoti-sarmah--higgsfield-ltx-video-ltxvideoservice-g-265391.modal.run`
- App: `higgsfield-ltx-video` (ap-JEDfc0IUcIRqLD2HUUmdLA)

Live check used a real photo (`https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1280`, a beach at sunset) and the prompt `"Slow push in toward the horizon. Keep the same scene, subject and lighting as the image. Cinematic, smooth camera motion, natural detail."`. Two POST calls were made back-to-back (via a throwaway Modal helper function so the `MODAL_WEBHOOK_SECRET` never touched the local shell — the local shell has no webhook secret set; it is stored only as the `modal-auth` Modal secret). The endpoint's fastapi web function issued a `303` "still starting" redirect on the very first request, which the client followed with `follow_redirects=True`.

| Call | Wall-clock seconds |
|---|---|
| 1st (container start + generate) | 64.5s |
| 2nd (same warm container) | 63.3s |

Both calls returned `width=960, height=544, duration_ms=5042` — the pipeline loads once at `@modal.enter()` and both calls hit the already-loaded container (the `ltx-weights` volume already had the model cached from earlier spike work, so the two times are close; the `load_seconds` field in the response is reported as `0.0` because loading happens outside the timed request in this design — see Open issues).

SSIM (frames 0, 60, last of the clip vs. the same `fit_to_output`-fitted input image, via `ffmpeg -lavfi ssim`):
| Frame | SSIM (All) |
|---|---|
| 0 | 0.893 |
| 60 | 0.600 |
| 120 (last) | 0.651 |

All three >= the 0.45 bar. The 3-frame tile at `docs/verification/T-011-1/frames.png` shows a smooth push-in with the horizon, sky and shoreline staying consistent — no visible scene cut.

## Acceptance checks
- [x] Unit tests for `fit_to_output`: landscape, portrait, square, and a tiny image — 5 tests, all pass.
- [x] Endpoint deployed; same request and response contract; the pipeline loads once (the `@modal.enter()` hook only runs on container start, not per request).
- [x] SSIM >= 0.45 on frames 0, 60 and last, and no scene cut visible in the tile.
- [x] `ltx_spike.py` unchanged.

## Open issues / guesses / things skipped
- The endpoint's `load_seconds` field is now always `0.0` since the model load happens in `@modal.enter()`, outside the per-request timer (the old spike's endpoint loaded on every request and reported real load time). `apps/api/app/adapters/modal_adapter.py` doesn't read `load_seconds`/`generate_seconds` at all (only `video_base64`, `width`, `height`, `duration_ms`), so this doesn't break the contract, but flagging it since the field's meaning changed.
- Because the `ltx-weights` volume already had the model cached from prior spike runs, the "cold" call's 64.5s doesn't include a multi-minute weight download — it mostly reflects `@modal.enter()` + generation. A truly cold (empty-volume) timing wasn't measured; the brief only asked for cold vs. warm wall-clock times from calling twice, which is reported above.
- Did not touch Railway or `MODAL_ENDPOINT_URL`; that swap is the orchestrator's job per the brief.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| LTX-2.5 image->clip Modal endpoint loads the pipeline once, crops/fits input to output aspect, keeps the existing request/response contract | `apps/gpu/ltx_video.py`, `apps/gpu/fit_input.py` | `apps/api/.venv/bin/python -m pytest apps/gpu/tests -q` (5 passed) + live render, SSIM >= 0.45 on all 3 frames | 2026-09-26 |
