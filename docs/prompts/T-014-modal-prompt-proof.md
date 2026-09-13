# Brief T-014: prompt-conditioned generation proof on the live URL

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Depends on: `docs/prompts/T-013-modal-adapter.md` (do not start until T-013 is DONE)
- Prompt already flows end to end: `apps/api/app/services/generation_runs.py` builds
  `GenerationRequest.prompt` from `job.prompt`; the spike forwards it to the pipeline.
- Live surface: `docs/STATUS.md` § WORKS (the public Railway URL), `scripts/smoke-generation`
- pixovid's caller does submit → poll → download and surfaces provider cost:
  `pixovid/apps/backend/src/lib/openrouter.ts` (shape reference)

## Goal
Prove the product is truly prompt-conditioned: two different prompts on the same input image
produce two visibly different clips, and the prompt actually reaches the model. Keep
`local-motion` the default so nothing else changes for normal traffic.

## Allowed files (touch nothing else)
- `apps/api/app/adapters/modal_adapter.py` (only to make sure the prompt is passed, not dropped)
- `scripts/smoke-generation` (add an opt-in prompt check, default behaviour unchanged)
- `docs/tasks/T-014/{brief,report}.md`, `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md`
- `.agent-logs/*T-014*`

## Must reuse
- `scripts/smoke-generation` — do not write a new smoke script; add one labelled step.
- The presigned download URL for the input image (`GenerationRequest.input_image_url`).
- `MODAL_ENDPOINT_URL` and the proven T-013 call shape.

## Acceptance checks
- [ ] The same input image with prompt A ("slow dolly in") and prompt B ("orbit around the
      subject") yields two clips whose first frames differ (compare bytes/hash, not eyes).
- [ ] The clip duration/size matches the T-012/T-013 shape (121 f, ~5 s, 960×544).
- [ ] `GENERATION_BACKEND` default in `.env.example` is still `mock`/`local-motion`; prod
      flips it explicitly. No contract change.
- [ ] Total spend of this task is measured and recorded honestly (~$0.4 for two clips).
- [ ] No secrets in chat, report, commit, or logs.

## Verify command (paste its full output in report.md)
```
GENERATION_BACKEND=mock uv --directory apps/api run pytest -q
SMOKE_STATUS_TIMEOUT=600 scripts/smoke-generation --base-url <live-or-local> --check-prompt
```
The second command is the paid/live one. If the environment has no Modal config, mark it
UNVERIFIED and say exactly what is missing; do not simulate it.

## Out of scope
- Changing the default backend, new presets, templates (T-021/T-022), face swap (T-023).
- Touching `packages/contracts/openapi.json`.

## Report
Write `docs/tasks/T-014/report.md` using `docs/templates/report.md`. ONE plain commit.
Do not mark your own work reviewed.
