# Brief T-011-1: Faithful, warm LTX clip endpoint on Modal

**Role:** implementer (GPU) · **Depends on:** — · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md`.

## Goal
Spec 011 AC-1, AC-3 and AC-4. A new Modal app serves image → clip with the model loaded once per container. It crops the input to the output aspect, renders portrait or landscape or square to match the input, and always passes the prompt through. The live endpoint contract stays the same:
- request: POST JSON `{image_url, prompt}` with `Authorization: Bearer $MODAL_WEBHOOK_SECRET`;
- response: whatever `apps/api/app/adapters/modal_adapter.py` parses today. Read it and keep it exactly.

## Allowed files
- `apps/gpu/ltx_video.py` (new; leave `ltx_spike.py` untouched as the historical spike)
- `apps/gpu/fit_input.py` (new, pure Pillow: `fit_to_output(image) -> (image, width, height)`)
- `apps/gpu/tests/test_fit_input.py` (new)
- `docs/tasks/T-011-1/*`

## The change
1. **`fit_to_output`:** choose landscape 960×544, portrait 544×960, or square 704×704 from the input's aspect (thresholds ≥ 1.2 and ≤ 0.83). Center-crop to that aspect, then resize with LANCZOS. Return the image and its size. Every dimension must be a multiple of 32.
2. **`ltx_video.py`:** copy the working pieces of `ltx_spike.py`'s `generate_clip_endpoint`, but:
   - use `@app.cls(gpu="H100", …)` with `@modal.enter()` loading `LTX2ImageToVideoPipeline` once (keep the same volume, secrets and model id);
   - `scaledown_window` of about 300 s;
   - a `@modal.fastapi_endpoint(method="POST")` method with the same auth, the same request and the same response shape;
   - the image goes through `fit_to_output`, and the width and height come from it;
   - reject an empty prompt with 422 (the API always sends one after T-011-2);
   - keep `DEFAULT_NEGATIVE_PROMPT`, the distilled sigmas and `CLIP_FRAMES`.
3. **Deploy:** `modal deploy apps/gpu/ltx_video.py`. Put the printed endpoint URL in the report. **Don't** change Railway; the orchestrator swaps `MODAL_ENDPOINT_URL`.
4. **Live check (one or two renders only):**
   - Download a real photo input: use `https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1280` (a beach), or any real landscape JPEG.
   - Call your endpoint with the prompt `"Slow push in toward the horizon. Keep the same scene, subject and lighting as the image. Cinematic, smooth camera motion, natural detail."`.
   - Extract frames 0, 60 and last with ffmpeg and compute SSIM of each against the fitted input. Use `ffmpeg -lavfi ssim`, or scikit-image if it's already available; no new repo dependencies.
   - Report the three SSIM values, the clip's dimensions, and the cold and warm wall-clock times (call it twice). Save a 3-frame tile to `docs/verification/T-011-1/frames.png`.

## Acceptance checks
- [ ] Unit tests for `fit_to_output`: landscape, portrait, square, and a tiny image
- [ ] Endpoint deployed; same request and response contract; the pipeline loads once (the warm call is faster, with times reported)
- [ ] SSIM ≥ 0.45 on frames 0, 60 and last, and no scene cut visible in the tile
- [ ] `ltx_spike.py` unchanged

## Verify command
```
apps/api/.venv/bin/python -m pytest apps/gpu/tests -q && apps/api/.venv/bin/python -m py_compile apps/gpu/ltx_video.py apps/gpu/fit_input.py
```
(If Pillow is missing from `apps/api/.venv`, say so and use `uv run --with pillow --with pytest`.)
