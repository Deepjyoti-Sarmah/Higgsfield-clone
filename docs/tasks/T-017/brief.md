# Brief T-017: Real text→image on our own GPU (FLUX.1-schnell on Modal)

**Role:** implementer (strong model) · **After T-033** (the budget guard must exist before a second paid backend goes live)

## Problem
`/create/image` is fully built — routes, credits, SSE, library — but `apps/api/app/adapters/placeholder_image_adapter.py` writes a PNG whose own docstring says "obviously placeholder content". A half-real feature in the nav is worse than none.

## Goal
Real images, generated on **our own Modal GPU**, through the existing `ImageModelAdapter` port. Nothing else in the pipeline changes.

## Why this model
**`black-forest-labs/FLUX.1-schnell`** — Apache 2.0, so commercially safe. FLUX.1-dev is non-commercial and LLaDA-Image never stated a licence; do not use either. 4 steps, first-class in `diffusers`, ~24 GB in bf16.

**Pin the GPU to H100.** It does not fit A10G, and T-013 already OOM'd once on H100 with a full-CUDA load — mirror whatever offload setting `apps/gpu/ltx_spike.py` settled on.

## The work
1. **`apps/gpu/flux_image.py`** — a **separate Modal function** from the video one (separate container, so the two models never share a cold start). Reuse the existing `huggingface` + `r2` secrets and the weights Volume. Signature:
   `generate_images(prompt, width, height, steps, count) -> {images_base64: [...], width, height}`.
   Batch all `count` images in one pipeline call.
2. **`apps/api/app/adapters/modal_image_adapter.py`** — implements the `ImageModelAdapter` Protocol in `app/adapters/image_model_adapter.py`. Mirror `modal_adapter.py`: bearer auth, POST, validate the response, decode into `request.work_dir`, return `ImageGenerationResult(image_paths, width, height)`. The worker uploads them exactly as it does today.
3. **Dimension + step mapping** in ONE place (extend `app/services/image_options.py` if it fits, otherwise a new `app/domain/image_dimensions.py`):

   | aspect_ratio | size |
   |---|---|
   | square | 1024×1024 |
   | portrait | 832×1216 |
   | landscape | 1216×832 |
   | wide | 1344×768 |
   | vertical | 768×1344 |

   `quality`: standard → 4 steps, high → 8 steps.
4. **Separate backend switch.** `select_image_adapter` in `app/adapters/backend_selection.py` currently keys off `generation_backend` (the *video* setting). Add `IMAGE_GENERATION_BACKEND` (`placeholder` | `modal` | `mock`) so image and video backends are independent. Default stays `placeholder` until you have measured numbers.
5. **Fallback:** a Modal failure or timeout falls back to `PlaceholderImageAdapter` — and, per T-033's rule, the result is labelled so a placeholder is never presented as a real generation.

## Allowed files
- `apps/gpu/flux_image.py` (new)
- `apps/api/app/adapters/{modal_image_adapter.py,backend_selection.py}`
- `apps/api/app/{settings.py,services/image_options.py}`, `apps/api/app/domain/image_dimensions.py` (if needed)
- `.env.example`
- `apps/api/tests/test_modal_image_adapter.py` (new), `apps/api/tests/test_backend_selection.py`
- `docs/tasks/T-017/report.md`, `docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md`

## Must reuse
- The `ImageModelAdapter` Protocol — **do not edit it**.
- `modal_adapter.py`'s auth/validation/error handling shape.
- The existing Modal secrets and weights Volume.

## Acceptance checks
- [ ] A 4-image job returns 4 real, visibly different images matching the prompt
- [ ] **Measured and recorded:** cold-start seconds, warm seconds per job, and $/job at the H100 rate
- [ ] Each aspect ratio produces the exact pixel size in the table
- [ ] Unconfigured endpoint → falls back to placeholder, job still succeeds, result labelled as a placeholder
- [ ] `IMAGE_GENERATION_BACKEND` switches backends without touching video
- [ ] `openapi.json` unchanged (byte-identical)
- [ ] No paid calls in pytest; no secrets in code, logs or report

## Verify command (paste full output in report.md)
```
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
scripts/check-standards
```
Plus a clearly-labelled **paid** probe (~$0.01–0.05), recording cold and warm timings:
```
modal run apps/gpu/flux_image.py --prompt "a neon-lit tokyo alley at night" --count 4
```
If you cannot run it, mark the live half **UNVERIFIED**. Do not simulate results.

## Out of scope
- Image-to-image, reference images, upscaling, editing, face swap.
- Changing the video backend or the image-jobs contract.

## Report
`docs/tasks/T-017/report.md` with the timing + cost table. One commit, plain message, no attribution trailers, include `.agent-logs/`.
