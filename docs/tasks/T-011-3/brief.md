# Brief T-011-3: Face swap endpoint on Modal

**Role:** implementer (GPU) · **Depends on:** — · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md`.

## Goal
Spec 011 AC-5, the model half. A Modal endpoint takes a **source** face image URL and a **target** image URL and returns the target with the source face swapped in, after a face-restoration pass. The idea follows Pixovid's FaceFusion setup (a swapper plus a GFPGAN enhancer), but with our own code.

## Allowed files
- `apps/gpu/face_swap.py` (new: the Modal app)
- `apps/gpu/face_swap_core.py` (new: pure-ish swap pipeline functions, importable without Modal)
- `apps/gpu/tests/test_face_swap_core.py` (new; unit-test only the pure parts, such as face picking and box maths)
- `docs/tasks/T-011-3/*`, `docs/verification/T-011-3/*`

## The change
1. **Image:** `modal.Image.debian_slim()` with `pip_install("insightface==0.7.3", "onnxruntime-gpu", "opencv-python-headless", "numpy<2", "huggingface_hub", "gfpgan` or an onnx GFPGAN")`. Pick what works and pin the versions in the report.
2. **Models** go on a Modal Volume, downloaded once in `@modal.enter`:
   - detection and landmarks: insightface `buffalo_l`;
   - swapper: `inswapper_128_fp16.onnx`;
   - enhancer: `gfpgan_1.4.onnx`, both from the Hugging Face repo `facefusion/models-3.0.0`.
   Verify the file names with `huggingface_hub.list_repo_files`. If they aren't there, use another public mirror and name it in the report.
3. **Pipeline** (`face_swap_core.py`):
   - detect faces in the source (take the largest) and in the target (swap **every** face, or the largest; document your choice);
   - swap with inswapper, run GFPGAN on each swapped face crop, then paste it back with a feathered mask;
   - return PNG bytes.
   - No face in the source or target → a typed error with the message "No face found in the face image" or "No face found in the target image".
4. **Endpoint:** `@modal.fastapi_endpoint(method="POST")` on an `@app.cls(gpu="A10G" or "L4")`.
   - Request: `{source_url, target_url}` with bearer auth using the same `modal-auth` secret, `MODAL_WEBHOOK_SECRET`.
   - Response: `{"image_base64": "...", "width": w, "height": h}`, or a 422 with `{"detail": "<user-safe message>"}` for no-face.
5. **Deploy** with `modal deploy apps/gpu/face_swap.py` and put the URL in the report.
6. **Live check:**
   - Make two portraits with the existing FLUX endpoint (the URL is in `docs/WORKLOG.md` 2026-09-14 07:40; call it the way `apps/api/app/adapters/modal_image_adapter.py` does). Prompts: "studio portrait photo of a smiling woman, front facing" and "photo of a man in a denim jacket in a park, front facing". Or use two public-domain portrait photos.
   - Swap A's face onto B.
   - Save `source.png`, `target.png` and `result.png` to `docs/verification/T-011-3/`, and include the timing and a no-face 422 check (a landscape photo as the source).

## Acceptance checks
- [ ] The result shows B's body, pose and background with A's face, looking natural (no mask seams). Describe it honestly
- [ ] The no-face case returns 422 with the user-safe message
- [ ] The licences of the models used are named in the report (inswapper is non-commercial)

## Verify command
```
apps/api/.venv/bin/python -m py_compile apps/gpu/face_swap.py apps/gpu/face_swap_core.py && (apps/api/.venv/bin/python -m pytest apps/gpu/tests/test_face_swap_core.py -q || uv run --with numpy --with pytest pytest apps/gpu/tests/test_face_swap_core.py -q)
```
