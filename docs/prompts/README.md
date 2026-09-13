# Prompts: port the pixovid patterns onto higgsfield (share into any AI agent)

This folder turns the working parts of `pixovid/` into six **task packets** you can paste
into different agents. Each file follows `docs/templates/delegation-brief.md` and points at
real paths in this repo. Nothing here is a contract change; every task ends in one commit.

## How to use a prompt
1. Pick **one** prompt file. Paste the whole file into the agent as its first message.
2. The agent writes `docs/tasks/<id>/report.md` and commits (the brief says so).
3. A **different** model re-runs the verify command before the task is DONE
   (`docs/AGENTS.md` roles; `docs/playbooks/task-run.md`).
4. After `docs/PLAN.md`/STATUS are updated, the task is closed.

> Prefer `scripts/agent-run <tool> <task-id>` for non-Claude CLIs so the transcript lands
> in `.agent-logs/` (the assignment requires prompt+response capture).

## What actually transfers from pixovid

| pixovid pattern | Source (read it, do not run it) | higgsfield home | Prompt |
|---|---|---|---|
| Server-side provider call with submit + poll, download bytes to disk | `pixovid/apps/backend/src/lib/openrouter.ts` | `apps/api/app/adapters/modal_adapter.py` (T-013) | `T-013-modal-adapter.md` |
| Prompt-conditioned generation, honest per-run cost | `pixovid/apps/backend/src/lib/openrouter.ts` | `apps/gpu/ltx_spike.py`, smoke | `T-014-modal-prompt-proof.md` |
| Template = ordered blocks, admin authoring, effects gallery | `pixovid/apps/backend/src/routes/adminTemplates.ts`, `pixovid/spec/04-video-templates.md` | new spec + `preset`/`job` | `T-021-effects-spec.md` |
| Multi-track timeline, crop, bake, pure `buildTimelineSegments` | `pixovid/spec/12-timeline-editor-learnings.md` | `scripts/` + web + worker | `T-022-timeline-remotion.md` |
| Face swap (self-hosted service, CPU) | `pixovid/infra/facefusion/server.py`, `pixovid/apps/backend/src/lib/facefusion.ts` | Modal GPU (T-023) | `T-023-face-swap.md` |
| Credits packs + order + verify + webhook backstop | `pixovid/apps/backend/src/lib/credits.ts`, `pixovid/apps/backend/src/routes/credits.ts` | `apps/api/app/services/credits.py` (T-024) | `T-024-real-billing.md` |

## Why these six, in this order
1. **T-013 + T-014 close the "real AI" gap** — a real Modal clip already landed (T-012);
   the adapter is the only thing between the spike and the live product. Highest value.
2. **T-021/T-022 give the product a differentiated surface** (effects/templates), which is
   exactly the shape `pixovid/` already proved at a smaller scale.
3. **T-023 face swap** reuses the Modal pattern from T-013, so it is cheap once that exists.
4. **T-024 billing** is last: it is contract-visible and needs human Razorpay credentials.

## Hard rules that apply to every prompt (from `AGENTS.md`)
- Truth hierarchy: running code + tests > `packages/contracts/openapi.json` > design > spec > PLAN > chat.
- Only touch the files the brief allows. One commit per task, plain message, no attribution trailers.
- Never commit secrets; config arrives by env var, names listed in `.env.example`.
- Never run paid generation in tests. `GENERATION_BACKEND=mock` (or `local-motion`) in tests.
- `scripts/check-standards` must pass; files ≤ 200 lines, comments ≤ 3 lines.
- A different model reviews the work; never mark your own reviewed.

## Suggested wave plan for an orchestrator
- **Wave 1 (parallel):** T-013 (API/GPU) + T-021 (spec only). Disjoint files.
- **Wave 2 (parallel):** T-014 (API) + T-022 implementers (web/scripts). Disjoint files.
- **Wave 3:** T-023 (after T-013 proves the Modal call shape) + T-024 (after a human adds keys).
- **After every wave:** append one line to `docs/WORKLOG.md`, update `docs/STATUS.md` with a
  path + verify command, tick the PLAN row. A human tick is the only thing that ends a wave.
