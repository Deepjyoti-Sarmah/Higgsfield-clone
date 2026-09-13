# Brief T-021: spec + contract-first design for an effects/templates gallery

You are the **orchestrator/spec author** for this one task (no product code yet). Your first steps:
1. Read `AGENTS.md`, `docs/STANDARDS.md`, `docs/playbooks/spec-new.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Inspiration (proven shape, smaller scale): `pixovid/spec/04-video-templates.md`,
  `pixovid/spec/05-video-templates-decisions.md`, `pixovid/apps/backend/src/routes/adminTemplates.ts`
- Existing primitives to build on: `apps/api/app/domain/preset_catalog.py`, the `preset` table,
  `apps/web/src/features/explore/` (gallery already groups presets by category)
- Contract: `packages/contracts/openapi.json` (currently 15 paths)
- Truth hierarchy and Definition of Done: `AGENTS.md`

## Goal
Write `docs/specs/010-effects/{spec,design,tasks}.md` for an **Effects** feature: a curated,
admin-authored "effect" that bundles a preset + a fixed prompt/params and appears in the
Explore gallery as one click-to-use card. Ship **contract-first**: publish the new paths as
**501 stubs** with final schemas, then write a brief per parallel-safe task, exactly like T-003-0.

## Non-negotiable design constraints
- An **effect is not a new generation pipeline**: it resolves to the existing
  `POST /api/v1/jobs` flow (preset_slug + prompt + optional input). Reuse `job`, `ledger_entry`,
  `job_step`; do not add a parallel generation path.
- Prefer **no migration** if a small `effect` table can be modelled on the existing pattern;
  if a migration is required, number it `0005` and say why in the design.
- Admin authoring is a **P1/P2** slice in the spec, but the contract for public read
  (`GET /api/v1/effects`) is P0 and must ship first as a 501 stub.
- Keep pixovid's lesson: **the provider encodes constraints; read them, don't hardcode.**
  Effect params should reference existing preset metadata rather than duplicating it.

## Allowed files (touch nothing else)
- `docs/specs/010-effects/{spec,design,tasks}.md` (new)
- `packages/contracts/openapi.json` + `apps/api/app/schemas/effects.py` + a new router with 501 stubs
- `apps/api/tests/test_effects_contract.py` (new, stub-level only)
- `docs/tasks/T-021-*/brief.md` (the per-task packets it writes)
- `docs/tasks/T-021/{brief,report}.md`, `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md`
- `.agent-logs/*T-021*`

## Acceptance checks
- [ ] Every API path the design names exists in `packages/contracts/openapi.json`; stubs answer 501.
- [ ] The contract diff is **additive only** — `git diff --exit-code` on a re-export is clean.
- [ ] `tasks.md` assigns every touched file to exactly one task (run the file-overlap check T-003-0 used).
- [ ] Each new task has a verify command that a *different* model can re-run.
- [ ] `scripts/check-standards` passes; no file > 200 lines.

## Verify command (paste its full output in report.md)
```
python3 -c "import json;print(len(json.load(open('packages/contracts/openapi.json'))['paths']))"
ls docs/tasks | grep T-021
scripts/check-standards
```
plus the contract-diff command from T-005-0/T-008-0 and a live 501 probe of the new stubs.

## Out of scope
- Implementing the effects feature (the briefs it writes do that), UI components, admin editor.
- The timeline/Remotion editor (T-022) and any real-model work.

## Report
Write `docs/tasks/T-021/report.md` using `docs/templates/report.md`. ONE plain commit.
Do not mark your own work reviewed.
