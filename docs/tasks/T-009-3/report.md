# Report T-009-3

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `apps/api/app/adapters/image_model_adapter.py` (new, 27 lines): the port — `ImageGenerationRequest {job_id, prompt, aspect_ratio, quality, count, work_dir}`, `ImageGenerationResult {image_paths, width, height}`, `ImageModelAdapter(Protocol) {name, generate_image}`. The error types are imported from `model_adapter.py`, not redefined.
- `apps/api/app/adapters/png_placeholder.py` (new, 37 lines): `write_placeholder_png(path, width, height, seed)` — a deterministic RGB gradient encoded with stdlib `zlib` + `struct` only (signature, `IHDR`, one `IDAT`, `IEND`, real CRCs). No Pillow, no new dependency. Seed-sensitive: the blue channel is `(seed*37 + x*3 + y*5) % 256`.
- `apps/api/app/adapters/placeholder_image_adapter.py` (new, 51 lines): `PlaceholderImageAdapter` (writes `image-{position}.png` per image at `IMAGE_PIXEL_SIZES[aspect]`, seed from `(job_id, position)`, file writes via `asyncio.to_thread`) and `UnconfiguredImageAdapter` (raises `BackendNotConfiguredError("Image generation is not configured (backend=…)")`).
- `apps/api/app/adapters/backend_selection.py` (edit, 16 → 29 lines): `+ select_image_adapter(settings)` — `mock`/`local-motion` → `PlaceholderImageAdapter`, `modal`/`openrouter` → `UnconfiguredImageAdapter`. `select_model_adapter` (video) is byte-identical and its existing tests still pass.
- `apps/api/tests/test_image_backend.py` (new, 107 lines): 14 tests.
- `docs/tasks/T-009-3/report.md`: this report.

## Reused
- `GenerationError` / `BackendNotConfiguredError` from `model_adapter.py` (one error vocabulary for both adapters; the worker's existing failure path turns either into a refund).
- `domain/image_rules.IMAGE_PIXEL_SIZES` (T-009-0) as the single source of aspect dimensions.
- `Settings.generation_backend`, and the test style of `tests/test_backend_selection.py`.
- No new dependency: `zlib` + `struct` are stdlib.

## Verify output (full paste, no summarising)
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
docker exit=0
All checks passed!
ruff exit=0
Success: no issues found in 35 source files
mypy exit=0
........................                                                 [100%]
24 passed in 2.51s
pytest exit=0
wrote packages/contracts/openapi.json
export exit=0
contract-diff exit=0
check-standards: ok (0 violations)
standards exit=0
```
`24 passed` = my 14 + the 10 existing `test_backend_selection.py` tests. The contract is byte-identical (this task adds no route).

**Proof the placeholder writes a real PNG** (not a renamed fixture), run directly:
```
$ uv --directory apps/api run python -c "… select_image_adapter(Settings(generation_backend='local-motion')) …"
image-1.png: 614820 bytes signature=b'\x89PNG\r\n\x1a\n' IHDR=640x360
image-2.png: 614851 bytes signature=b'\x89PNG\r\n\x1a\n' IHDR=640x360
backend: local-motion | result: 640 x 360
```
The different byte sizes for the same dimensions are the per-position seed, and `test_the_same_job_id_renders_identical_bytes` pins the determinism.

## Standards check
```
check-standards: ok (0 violations)
```
Sizes: `image_model_adapter.py` 27 · `png_placeholder.py` 37 · `placeholder_image_adapter.py` 51 · `backend_selection.py` 29 · `test_image_backend.py` 107 — all ≤200. Functions are ≤15 lines; `mypy --strict` green over 35 files (was 32; the three new adapter modules).

## Acceptance checks
- [x] the produced file is a **real PNG**: the test asserts the 8-byte signature, the `IHDR` chunk and that the decoded width/height equal `IMAGE_PIXEL_SIZES[aspect]` for all five ratios; the direct run above shows the same.
- [x] deterministic: same `(job_id, position, aspect)` → identical bytes; `test_the_writer_is_deterministic_and_seed_sensitive` also proves two different seeds differ.
- [x] `select_image_adapter` never returns a video adapter (it returns only the two image classes) and `select_model_adapter` is unchanged — its 10 tests still pass, including the `modal`/`openrouter` "not configured" cases.
- [x] `modal`/`openrouter` raise `BackendNotConfiguredError`, which the existing worker failure path converts into a job failure + `RELEASE` refund.
- [x] `scripts/export-openapi && git diff --exit-code` → byte-identical.
- [x] ruff (`All checks passed!`), mypy strict (35 files) and the focused suite green.

## Open issues / guesses / things skipped
- **This is a placeholder, not a model.** It produces an obviously synthetic gradient; D-014 and spec AC-10 require the page to caption it and the API to expose `backend`. Nothing here fakes a real model — `modal`/`openrouter` still refuse.
- **File size.** A 640×360 gradient compresses to ~600 KB because the blue channel varies per pixel; a 4-image job uploads ~2.4 MB. Fine for local MinIO/R2 and the demo, but a real (or more compressible) placeholder would be smaller — recorded, not fixed.
- **Cost of the pure-Python loop.** Writing one 640×360 PNG takes ~100-200 ms (the focused suite, which renders ~10 images, runs in ~2.5 s). Acceptable for a placeholder backend; a real adapter streams from the model instead.
- **`quality` is accepted but unused** by the placeholder (it only affects the credit cost). Documented behaviour: the placeholder does not model quality.
- **The aspect size map is in `domain/image_rules.py`** (T-009-0), so the adapter and the future read route agree; a fallback of 512×512 covers an unknown ratio defensively.
- No commit (per the brief). No change to the schemas, the routes, the worker, the services or any web file.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Image backend port + placeholder: `ImageModelAdapter` (`generate_image`), a dependency-free deterministic PNG writer, `PlaceholderImageAdapter` for `local-motion`/`mock` (real PNGs at the right aspect) and `UnconfiguredImageAdapter` for `modal`/`openrouter` ("not configured" → refund) | `apps/api/app/adapters/{image_model_adapter,png_placeholder,placeholder_image_adapter,backend_selection}.py`, `apps/api/tests/test_image_backend.py` | `docker compose up -d --wait db && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q tests/test_image_backend.py tests/test_backend_selection.py && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` → 24 passed, mypy clean (35 files), contract byte-identical, 0 violations; direct run shows `\x89PNG` + IHDR 640×360 | 2026-09-13 23:11 |
