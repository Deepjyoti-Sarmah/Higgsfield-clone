# Brief T-011-2: Always send the video model a real prompt

**Role:** implementer (API) · **Depends on:** — · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md`.

## Goal
Spec 011 AC-2. `ModalAdapter` sends `request.prompt or ""` today, so a blank prompt means the model gets nothing. Build the prompt from the preset's motion description plus the user's text plus a fixed "keep the scene" and quality clause.

## Allowed files
- `apps/api/app/domain/motion_prompts.py` (new)
- `apps/api/app/adapters/modal_adapter.py`
- `apps/api/tests/test_motion_prompts.py` (new)
- `docs/tasks/T-011-2/*`

## The change
1. **`compose_clip_prompt(preset_slug: str, user_prompt: str | None) -> str`** (pure):
   - The motion sentence comes from `PRESET_CATALOG`'s `description` (`domain/preset_catalog.py`), with an unknown slug falling back to "Subtle, slow camera motion."
   - If `user_prompt` is non-empty after strip, append it verbatim, trimmed to 300 characters.
   - Then append the constant `SCENE_CLAUSE`: "Keep the same subject, scene, framing and lighting as the input image; no new objects, no scene change."
   - Then `QUALITY_CLAUSE`: "Cinematic, smooth camera motion, natural detail, stable exposure."
   - Join with single spaces. Never return an empty string.
2. **`modal_adapter.py`:** send `compose_clip_prompt(request.preset_slug, request.prompt)` instead of `request.prompt or ""`. Nothing else changes.
3. **Tests:**
   - A blank prompt still contains the preset description and both clauses.
   - A user prompt is included.
   - An unknown slug falls back.
   - Long user text is trimmed.
   - The adapter posts the composed prompt: use the existing Modal adapter test pattern with a fake HTTP transport. Find it with `grep -rl ModalAdapter apps/api/tests`.

## Acceptance checks
- [ ] No contract change (`openapi.json` byte-identical after `scripts/export-openapi`)
- [ ] ruff, mypy and pytest green

## Verify command
```
docker compose up -d --wait db && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q tests/test_motion_prompts.py $(grep -rl --include='*.py' ModalAdapter apps/api/tests | sed 's#^apps/api/##' | tr '\n' ' ')
```
