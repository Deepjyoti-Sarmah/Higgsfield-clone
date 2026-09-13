# Brief T-003-6: Generation backends (local-motion, mock, modal, openrouter, selection)

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/003-generation-core/spec.md` (AC-8)
- Design: `docs/specs/003-generation-core/design.md` sections **ModelAdapter** (Protocol + backend table), **Presets catalog (12) and local-motion recipes** (canvas, constants, filter chain, commands, the recipe table), **Settings added**
- Decisions: D-002, D-003 in `docs/DECISIONS.md` (why modal/openrouter stay placeholders)
- Existing: `apps/api/app/adapters/model_adapter.py`, `apps/api/app/domain/preset_catalog.py` (both from T-003-1), `Dockerfile`

## Goal
`GENERATION_BACKEND=local-motion` turns an image into a real 5s, ≤720p, h264, faststart mp4 plus a poster with the preset's camera move; `mock` is instant; `modal` and `openrouter` fail clearly with "backend not configured".

## Allowed files (touch nothing else)
- `apps/api/app/adapters/{motion_recipes,local_motion_adapter,mock_model_adapter,modal_adapter,openrouter_adapter,backend_selection}.py`
- `apps/api/app/adapters/fixtures/mock-video.mp4`, `apps/api/app/adapters/fixtures/mock-poster.jpg`
- `Dockerfile` (install ffmpeg in the `app` stage: `apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*`)
- `apps/api/tests/{test_local_motion_adapter,test_backend_selection}.py`
- `docs/tasks/T-003-6/report.md`

## Behaviour notes
- **Recipes:** copy the 12 rows of the design table literally (zoom/x/y/margin/rotate/blur). T-003-0 rendered all of them on ffmpeg 7.1.4 in 0.7–2.8s each with no black corners; don't "improve" them without re-checking.
- **Filter builder:** `build_motion_filter(recipe, width, height) -> str` and `pick_canvas(input_width, input_height) -> tuple[int, int]` in `motion_recipes.py`. Pass the chain as ONE argv element (no shell).
- **Adapter:** `ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0`, then the two ffmpeg commands from the design via `asyncio.create_subprocess_exec`; capture stderr for logs only; user-facing errors exactly as in the design table. Return `GenerationResult` with width, height, `duration_ms=5000`.
- **Mock fixtures:** generate once with `ffmpeg -f lavfi -i color=c=gray:s=64x64:d=1:r=24 -c:v libx264 -pix_fmt yuv420p -movflags +faststart mock-video.mp4` and `ffmpeg -i mock-video.mp4 -frames:v 1 mock-poster.jpg`. `MOCK_GENERATION_FAILS=true` → `GenerationError("Mock failure")`.
- **Placeholders:** make no network calls. Messages exactly as in the design.
- **Selection:** `select_model_adapter(settings: Settings) -> ModelAdapter`; each adapter has a `name` equal to its `GENERATION_BACKEND` value.

## Must reuse
- `ModelAdapter`, `GenerationRequest`, `GenerationResult`, `GenerationError`, `BackendNotConfiguredError` (T-003-1), `PRESET_CATALOG` / `PresetDefinition` (T-003-1), `Settings`.

## Acceptance checks
- [ ] Recipe slugs == catalog slugs (12)
- [ ] For every preset (parametrized), a generated 640×400 jpg → mp4 with codec h264, width ≤ 1280, height ≤ 720, 120 frames, duration 5.0s ± 0.05, `moov` before `mdat`, and a non-empty poster jpg; a 400×640 png → 720×1280 (one preset is enough for portrait)
- [ ] A corrupt input file → `GenerationError` with the user-safe message; an unknown slug → `GenerationError("This preset isn't available.")`
- [ ] `mock` returns in < 1s; `MOCK_GENERATION_FAILS` raises
- [ ] `modal` / `openrouter` with empty credentials raise `BackendNotConfiguredError` whose message contains "not configured"
- [ ] `docker run --rm --entrypoint ffmpeg hf-clone -version` prints a version
- [ ] mypy strict clean on `app/adapters`

## Verify command (paste its full output in report.md)
```
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q tests/test_local_motion_adapter.py tests/test_backend_selection.py
docker build -t hf-clone .
docker run --rm --entrypoint ffmpeg hf-clone -version
scripts/check-standards
```

## Out of scope
- The worker loop, storage uploads, job status, credits (T-003-5); real Modal/OpenRouter calls (never in tests; D-003); preview videos for Explore (spec 006).

## Report
Write `docs/tasks/T-003-6/report.md` using `docs/templates/report.md`, then follow the definition of done in `AGENTS.md` (commit per the kickoff prompt, plain message, no trailers, include `.agent-logs/`).
