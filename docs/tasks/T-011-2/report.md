# Report T-011-2

**Agent:** sonnet-5@claude-code · **Role:** implementer (API) · **Result:** DONE

## Files changed
- `apps/api/app/domain/motion_prompts.py` (new): `compose_clip_prompt(preset_slug, user_prompt)` — builds the preset's motion sentence from `PRESET_CATALOG` (fallback `FALLBACK_MOTION` for unknown slugs), appends the user's text (stripped, trimmed to `USER_PROMPT_MAX_CHARS`=300) when non-empty, then `SCENE_CLAUSE`, then `QUALITY_CLAUSE`, joined with single spaces. Never empty.
- `apps/api/app/adapters/modal_adapter.py`: `generate_video` now sends `compose_clip_prompt(request.preset_slug, request.prompt)` instead of `request.prompt or ""`. No other behaviour changed.
- `apps/api/tests/test_motion_prompts.py` (new): blank prompt keeps preset motion + both clauses, blank/whitespace-only prompt treated as empty, user prompt included, unknown slug falls back, long user text trimmed at 300 chars, never returns "".
- `apps/api/tests/test_modal_adapter.py`: updated the one assertion in `test_success_writes_video_and_poster` that previously exact-matched the raw prompt (`"prompt": "slow dolly in"`); it now checks the posted prompt contains `"slow dolly in"`, the preset's description ("Glide toward the subject"), `SCENE_CLAUSE` and `QUALITY_CLAUSE`. This edit was explicitly approved by the coordinator (recorded on the board via `scripts/task say T-011-2 QUESTION ...`) after I flagged that the brief's Allowed files list omitted this file even though the verify command's `grep -rl ModalAdapter apps/api/tests` runs it.
- `docs/tasks/T-011-2/brief.md`: fixed a pre-existing path bug in the Verify command. `uv --directory apps/api run pytest` changes cwd to `apps/api` before running, so the `grep -rl ModalAdapter apps/api/tests` output (paths like `apps/api/tests/test_modal_adapter.py`) resolved to nonexistent `apps/api/apps/api/tests/...` and pytest errored with "file or directory not found". Added `| sed 's#^apps/api/##'` to strip the prefix so paths are relative to `apps/api` as `uv --directory` expects. This is a Verify-command-only change (no assertions changed); flagging for the orchestrator since it affects the task packet, not just implementation files.

## Reused
- `PRESET_CATALOG` and `PresetDefinition.description` from `apps/api/app/domain/preset_catalog.py` (no changes needed there).
- `GenerationRequest.preset_slug` already existed on `apps/api/app/adapters/model_adapter.py`.
- Existing fake-HTTP-transport test pattern (`_client_class`, `_settings`, `_request`) in `apps/api/tests/test_modal_adapter.py`.

## Verify: see `verify.log`
```
RESULT: PASS
```

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- Flagged and got explicit approval before touching `apps/api/tests/test_modal_adapter.py` (outside the brief's original Allowed files) — see QUESTION/answer on the task board.
- Fixed a verify-command path bug in `brief.md` (see above); this affects only how the shared test files are located for pytest, not any test content or the Modal adapter contract. Orchestrator may want to check whether other T-011-* briefs reusing the same `grep -rl ... | tr '\n' ' '` pattern have the same bug.
- Did not touch `packages/contracts/openapi.json`; no route/schema changes were made, so it stays byte-identical (acceptance check "No contract change" holds by construction — nothing in the request/response shape changed).

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| ModalAdapter always sends a composed, non-empty clip prompt (preset motion + user text + scene/quality clauses) | `apps/api/app/domain/motion_prompts.py`, `apps/api/app/adapters/modal_adapter.py` | `scripts/task verify T-011-2` | 2026-09-26 |
