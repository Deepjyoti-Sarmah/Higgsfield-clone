# Brief T-022: a composition/timeline editor (the pixovid timeline, adapted)

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links (the whole hard-won design is here — read it twice)
- `pixovid/spec/12-timeline-editor-learnings.md` — the data model, the pure
  `buildTimelineSegments` function, the ffmpeg gotchas, the drag/stale-closure hazards.
- `pixovid/spec/09-duration-per-model.md` and `pixovid/spec/11-video-ui-updates.md`
- `pixovid/apps/frontend/src/components/timeline/` (UI shape reference only)
- This repo's generation core: `apps/api/app/services/job_creation.py`,
  `apps/api/app/services/generation_runs.py`, `apps/api/app/adapters/local_motion_adapter.py`

## Goal
Design **and** implement the smallest honest slice of a timeline/composition editor:
an admin-authored "composition" made of ordered blocks (each block = one generated clip or
an uploaded mp4), composited into one output, with a **pure** segment resolver and a **bake**
path. Do the spec + contract first (same wave discipline as T-021), then the implementation.

## Decisions to copy from pixovid (do not reinvent)
- **Footprint invariant**: `endSec = startSec + ((cropEnd ?? duration) - cropStart)`, computed
  **server-side**, never trusted from the client. This killed a whole bug class.
- **Pure resolver**: `buildTimelineSegments(blocks) -> slices` with no ffmpeg and no network,
  unit-tested for overlay-tail, overlay-middle, gaps, and crop offset. Topmost track wins;
  black for gaps.
- **Same-track overlaps rejected, cross-track allowed.** Touching edges do not collide.
- **Generate the full duration, crop is non-destructive.** Bake reuses the same block renderer
  as the full composition.
- **Read constraints from the provider** (model durations/resolutions), never hardcode them.

## Higgsfield-specific adaptation
- The repo already has one renderer: `local-motion` (ffmpeg). Prefer extending that; a Remotion
  renderer is allowed only if it stays an adapter with the same result shape. State the choice
  in the design; do not add a second job system.
- Compositions must reuse `job`/`job_step`/`ledger_entry` (one step per block, one SETTLE).
  Charges follow the existing HOLD → SETTLE/RELEASE rules. No new billing path.
- The worker may run blocks sequentially; a composition of N blocks is N steps, not one giant step.

## Allowed files (touch nothing else)
- `docs/specs/010-effects/` … only if T-021 has frozen it; otherwise create
  `docs/specs/011-composition/` and do not edit T-021's files.
- `apps/api/app/domain/`, `apps/api/app/services/`, `apps/api/app/repositories/` (new files only)
- `apps/api/migrations/versions/0005_*.py` (only if the design proves a migration is required)
- `packages/contracts/openapi.json` + schemas + 501 stubs, `apps/api/tests/` (new)
- `apps/web/src/features/composition/`, `apps/web/src/api/`, `apps/web/src/App.tsx`
- `scripts/` (a renderer/smoke helper), `docs/tasks/T-022/{brief,report}.md`
- `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md`, `.agent-logs/*T-022*`

## Acceptance checks
- [ ] `buildTimelineSegments` is a pure function with unit tests for the four cases above.
- [ ] A 2-block composition renders one mp4 whose duration matches the computed footprint.
- [ ] A same-track overlapping drag is rejected server-side AND snaps back in the UI.
- [ ] Crop changes the footprint server-side; the client's stale `endSec` cannot desync it.
- [ ] Charges: one HOLD, one SETTLE on success, one RELEASE on failure; no double charge.
- [ ] Contract diff is additive only; `scripts/check-standards` passes (no file > 200 lines).
- [ ] Do not touch the timeline editor's *scope* without writing it in the design first.

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db minio && uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy
uv --directory apps/api run pytest -q tests/ -k "segment or composition"
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build
scripts/check-standards
```
plus a manual render of a 2-block composition with ffprobe output pasted in.

## Out of scope
- Real-payment billing (T-024), face swap (T-023), changing the Modal adapter (T-013).
- A full Premiere clone: keep the slice small, documented, and testable.

## Report
Write `docs/tasks/T-022/report.md` using `docs/templates/report.md`. ONE plain commit.
Do not mark your own work reviewed.
