# Report T-017

**Agent / model / tool:** implementer · deepseek-flash (DSH main session) · run_code/bash
**Result:** PARTIAL — implementation + unit tests DONE; the **paid GPU probe is BLOCKED/UNVERIFIED** on
Hugging Face gating (exact error below). Nothing is simulated.

## What is done
- `apps/gpu/flux_image.py` (new): Modal app `higgsfield-flux-image` on **H100**, `black-forest-labs/FLUX.1-schnell`,
  the shared `ltx-weights` volume and `huggingface` secret. `generate_images(prompt,width,height,steps,count)`
  batches all `count` images in one pipeline call and returns `{images_base64, width, height, load_seconds,
  generate_seconds}`; a bearer-protected `generate_images_endpoint` (from `modal-auth`) serves the API; the
  `@app.local_entrypoint()` writes PNGs to `build/flux/` and prints the timings (the brief's probe command).
  Offload mirrors T-013's settled `enable_model_cpu_offload()`.
- `apps/api/app/adapters/modal_image_adapter.py` (new): `ModalImageAdapter` implements the untouched
  `ImageModelAdapter` protocol — bearer auth, POST, validate, decode base64 into `work_dir` as
  `image-N.png`, return `ImageGenerationResult`. `FallbackImageAdapter` wraps it with the placeholder and
  mutates `name` to whichever backend actually produced the bytes (so the result is labelled honestly).
- `apps/api/app/domain/image_dimensions.py` (new): the FLUX sizes from the brief
  (1:1 1024², 4:5 832×1216, 3:2 1216×832, 16:9 1344×768, 9:16 768×1344) and 4/8 steps per quality.
- `apps/api/app/adapters/backend_selection.py`: `select_image_adapter` now keys off
  `IMAGE_GENERATION_BACKEND` (added in T-033) — `modal` → the fallback-wrapped real adapter, `mock` →
  placeholder named "mock", default `placeholder`. Video selection is untouched.
- `settings.py` + `.env.example`: `MODAL_IMAGE_ENDPOINT_URL`.
- Web labelling (one file outside the brief's list, called out): `ImageResultGrid.tsx` renders
  `GenerationBadge` (T-033) and treats the `placeholder` backend as the "Demo placeholder" notice, so a
  fallback is never shown as a real generation.

## Verify output (full paste, no summarising)
```
uv --directory apps/api run ruff check .   -> All checks passed!
uv --directory apps/api run mypy           -> Success: no issues found in 46 source files
uv --directory apps/api run pytest -q      -> 206 passed, 2 warnings
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json -> byte-identical
npm --prefix apps/web run test             -> 9 files / 60 tests passed
npm --prefix apps/web run build            -> built
scripts/check-standards                    -> check-standards: ok (0 violations)
```
New coverage: `test_modal_image_adapter.py` (endpoint/auth/params, all five aspect ratios, high=8 steps,
six malformed payloads, HTTP error, timeout) and the fallback/selection cases in `test_image_backend.py`.

## Paid probe — BLOCKED (UNVERIFIED, no results faked)
```
modal run apps/gpu/flux_image.py --prompt "a neon-lit tokyo alley at night" --count 4
huggingface_hub.errors.GatedRepoError: 403 Client Error.
Cannot access gated repo for url
https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/.../model_index.json.
Access to model black-forest-labs/FLUX.1-schnell is restricted and you are not in the authorized list.
```
FLUX.1-schnell is Apache-2.0 **but gated**: the HF account behind the Modal `huggingface` secret must open
the model page and accept the license. This is the same class of human step T-012 needed for LTX. Because the
container never reached the pipeline, **cold-start seconds, warm seconds and $/job are NOT measured** — the
acceptance check for measured numbers is open, not passed by guesswork.

## Acceptance checks
- [ ] A 4-image job returns 4 real images — **UNVERIFIED** (gated repo)
- [ ] Measured cold/warm/$ — **NOT MEASURED** (blocked before the pipeline loaded)
- [x] Each aspect ratio maps to the exact pixel size (parametrized unit test over all five)
- [x] Unconfigured endpoint → placeholder fallback, job succeeds, adapter `name` becomes `placeholder`
- [x] `IMAGE_GENERATION_BACKEND` switches image and video independently
- [x] `openapi.json` byte-identical
- [x] No paid calls in pytest; no secrets in code, logs or this report

## Open issues / guesses / things skipped
- **Blocker:** accept the FLUX.1-schnell license for the `huggingface` token, then re-run the one-line probe
  (est. ~$0.01–0.05). Until then the image backend default stays `placeholder`, so the live site is unaffected.
- `ImageResultGrid.tsx` is outside the brief's allowed-files list; the labelling rule ("per T-033's rule") is
  unreachable from the listed backend files, so it is documented rather than smuggled.
- `MODAL_IMAGE_ENDPOINT_URL` is intentionally **not** set on Railway: the default is `placeholder` and the
  brief says to keep it until the numbers exist.
- T-033's first live cutover exposed a latent T-013 bug (worker missing `httpx`); it is fixed in the
  `76b3d34` follow-up. This is why the live image adapter had briefly reported `image_backend=modal`
  (unconfigured) before this task's selection change.
- Not marked reviewed — a different model must review.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Real text→image backend: `ModalImageAdapter` (FLUX.1-schnell, H100) behind the untouched `ImageModelAdapter`, independent `IMAGE_GENERATION_BACKEND`, placeholder fallback that relabels itself; GPU probe blocked on HF model gating | `apps/gpu/flux_image.py`, `apps/api/app/adapters/{modal_image_adapter,backend_selection}.py`, `apps/api/app/domain/image_dimensions.py` | ruff + mypy + `pytest -q` -> 206 passed, openapi byte-identical, web 60 tests + build, `check-standards` ok; paid probe **UNVERIFIED** (`GatedRepoError 403` for FLUX.1-schnell) | 2026-09-14 04:55 |
