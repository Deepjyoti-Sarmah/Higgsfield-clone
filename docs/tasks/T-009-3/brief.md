# Brief T-009-3: API image backend — the port, the PNG placeholder and the adapter selection

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/009-image-create/spec.md` (AC-8, AC-10)
- Design: `docs/specs/009-image-create/design.md` § **Backend reality** (normative), **Data** (`image_rules`), **Flow 6**
- Existing: `apps/api/app/adapters/{model_adapter.py,backend_selection.py,mock_model_adapter.py,local_motion_adapter.py,modal_adapter.py}`, `apps/api/app/domain/image_rules.py` (created by T-009-0: the literals, `MAX_IMAGE_COUNT`, `image_credit_cost`, `IMAGE_PIXEL_SIZES`), `apps/api/app/settings.py` (`GenerationBackend`)
- Tests: `apps/api/tests/test_backend_selection.py` (the style to extend)

## Goal
A real, runnable image backend port: `local-motion` and `mock` write a valid deterministic PNG at the requested aspect; `modal`/`openrouter` fail with a clear "not configured" error. **No real model is promised or faked.**

## Allowed files (touch nothing else)
- `apps/api/app/adapters/image_model_adapter.py` (new)
- `apps/api/app/adapters/png_placeholder.py` (new)
- `apps/api/app/adapters/placeholder_image_adapter.py` (new)
- `apps/api/app/adapters/backend_selection.py` (edit)
- `apps/api/tests/test_image_backend.py` (new)
- `docs/tasks/T-009-3/report.md`

## Must do
- **`image_model_adapter.py`** — the port, mirroring `model_adapter.py`:
  - `@dataclass(frozen=True) ImageGenerationRequest {job_id: uuid.UUID; prompt: str; aspect_ratio: str; quality: str; count: int; work_dir: Path}`
  - `@dataclass(frozen=True) ImageGenerationResult {image_paths: list[Path]; width: int; height: int}`
  - `class ImageModelAdapter(Protocol): name: str; async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult: ...`
  - reuse `GenerationError`/`BackendNotConfiguredError` from `model_adapter.py` (do not redefine them).
- **`png_placeholder.py`** — dependency-free (stdlib `zlib` + `struct` only), mypy-strict:
  - `def write_placeholder_png(path: Path, width: int, height: int, seed: int) -> None` writing a valid RGB PNG (signature, `IHDR`, one `IDAT`, `IEND`, correct CRCs). Deterministic for a given `(width, height, seed)` — a smooth two-colour gradient derived from `seed` is enough; no randomness that changes between runs.
  - Keep it small and typed; no Pillow, no new dependency.
- **`placeholder_image_adapter.py`**:
  - `class PlaceholderImageAdapter` with `name` from the constructor and `generate_image` → `request.work_dir.mkdir(parents=True, exist_ok=True)`, then one `image-{position}.png` per image (`position` 1..count) at `IMAGE_PIXEL_SIZES[request.aspect_ratio]`, seeded per `(job_id, position)`, returning the paths + width/height. Use `asyncio.to_thread` for the file writes, like `MockModelAdapter`.
  - `class UnconfiguredImageAdapter` whose `generate_image` raises `BackendNotConfiguredError(f"Image generation is not configured (backend={name})")`.
- **`backend_selection.py`**: add `select_image_adapter(settings: Settings) -> ImageModelAdapter` — `mock` and `local-motion` → `PlaceholderImageAdapter(settings.generation_backend)`; `modal` and `openrouter` → `UnconfiguredImageAdapter(...)`. Do not change `select_model_adapter` (video) or the `GenerationBackend` literal.
- **Tests** (`test_image_backend.py`): the PNG has a valid signature and the exact dimensions requested (parse `IHDR` bytes back); the same seed produces identical bytes and a different seed does not; `count` files are produced and named by position; both `mock` and `local-motion` select a placeholder adapter, and `modal`/`openrouter` select one whose `generate_image` raises `BackendNotConfiguredError`.

## Acceptance checks
- [ ] `python -c` / a test proves the produced file is a **real PNG** (magic bytes + IHDR width/height match `IMAGE_PIXEL_SIZES[aspect]`) — not a renamed fixture
- [ ] deterministic: same `(job_id, position, aspect)` → identical bytes
- [ ] `select_image_adapter` never returns a video adapter and `select_model_adapter` is unchanged (its existing test still passes)
- [ ] `modal`/`openrouter` raise `BackendNotConfiguredError`, which the existing worker failure path turns into a refund
- [ ] `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` → byte-identical
- [ ] ruff, mypy (strict on `app/adapters`) and the suite are green

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q tests/test_image_backend.py tests/test_backend_selection.py && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards
```

## Out of scope
- Any real image model (LLaDA-Image/Modal/OpenRouter) — **do not write a fake "modal" image path**; `modal`/`openrouter` must keep failing as they do for video.
- The worker branch or the services/routes (T-009-4/T-009-5); the schemas/router (T-009-0); any web file.
- Editing `domain/image_rules.py` (T-009-0 owns it) — import from it instead.

## Report
Write `docs/tasks/T-009-3/report.md` using `docs/templates/report.md`. Don't commit; the orchestrator does.
