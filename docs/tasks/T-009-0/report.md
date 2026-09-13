# Report T-009-0

**Agent / model / tool:** orchestrator/designer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `docs/specs/009-image-create/spec.md` (new): problem/story, **AC-1 … AC-12**, all UI states, out of scope, and the explicit backend-reality statement (no real image model runs).
- `docs/specs/009-image-create/design.md` (new): the API contract first, a **Backend reality** table (which `GENERATION_BACKEND` produces an image), the additive `0004` data plan, the flow, the component tree with exact props, the shared-web-plumbing move table, the copy table, accessibility, the Files table, Reused, Risks and the AC map.
- `docs/specs/009-image-create/tasks.md` (new): waves `T-009-0 → (T-009-1 ∥ T-009-2 ∥ T-009-3) → (T-009-4 ∥ T-009-5 ∥ T-009-6) → T-009-7`; 24 distinct files; one declared sequential hand-off (`routers/image_jobs.py`).
- `docs/tasks/T-009-{1,2,3,4,5,6,7}/brief.md` (new): the seven delegation briefs (T-009-0 is this orchestrator task and has no brief, matching specs 005/007/008).
- `apps/api/app/domain/image_rules.py` (new): the aspect/quality literals, the allowed tuples, `MAX_IMAGE_COUNT = 4`, the unit costs (`10`/`15`) + `image_credit_cost(quality, count)`, and `IMAGE_PIXEL_SIZES` per aspect.
- `apps/api/app/schemas/image_jobs.py` (new): `ImageJobCreateRequest`, `ImageJobCreatedResponse`, `ImageJobResponse`, `ImageCreditCosts`, `ImageOptionsResponse`.
- `apps/api/app/routers/image_jobs.py` (new): the three 501 stubs, freezing handler names, signatures, status codes and responses maps for T-009-4.
- `apps/api/app/main.py` (edit): include the image router (before the SPA catch-all).
- `packages/contracts/openapi.json` (regenerated): **+451 / −0** — three new paths and five new schemas, no pre-existing entry touched.
- `docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md`, `docs/DECISIONS.md` (new **D-014**), `.agent-logs/2026-09-13_22-58_T-009-0_dsh-deepseek-flash.md`, `docs/tasks/T-009-0/report.md`: board/status/history sync.

## Reused
- API: `require_current_user`, `get_session`, `lock_user_row`, `find_job_by_idempotency_key`, `insert_job_step`, `notify_job_event`, `transition_job_status`, `complete_step_failure` (the generic RELEASE), the claim/lease/reaper loop, `JobEventBroker`/`stream_job_status_events`, `insert_asset`, `find_assets_by_ids`, `build_asset_url`, `InsufficientCreditsResponse`, `ErrorResponse`, `JobStatus`, and the existing `uq_job_user_idempotency_key` / `uq_job_step_job_kind` / `ix_job_user_created`.
- Web (designed for the later tasks): `apiClient` + generated schema, `api/guestSession.ts`, the spec-004 job watcher (moved to `api/` and made generic rather than re-implemented), `api/credits.ts` balance, `ui/Button`/`ButtonLink`/`EmptyState`, `SessionContextValue`.
- Process: `docs/templates/*`, and the spec 003/005/007/008 packaging pattern (contract frozen before any implementation task).

## Verify output (full paste, no summarising)
```
$ python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))"
/api/health
/api/v1/auth/guest
/api/v1/credits
/api/v1/credits/topup
/api/v1/image-jobs
/api/v1/image-jobs/{job_id}
/api/v1/image-options
/api/v1/jobs
/api/v1/jobs/{job_id}
/api/v1/jobs/{job_id}/events
/api/v1/me
/api/v1/presets
/api/v1/public/jobs/{job_id}
/api/v1/uploads
/api/v1/uploads/{asset_id}/complete

$ ls docs/tasks | grep T-009
T-009-0
T-009-1
T-009-2
T-009-3
T-009-4
T-009-5
T-009-6
T-009-7

$ scripts/check-standards
check-standards: ok (0 violations)
```

Extra evidence (run because AC-12 is the load-bearing constraint):
```
$ uv --directory apps/api run ruff check .
All checks passed!
$ uv --directory apps/api run mypy
Success: no issues found in 32 source files
$ scripts/export-openapi && git diff --numstat packages/contracts/openapi.json
wrote packages/contracts/openapi.json
451     0       packages/contracts/openapi.json
added paths    : ['/api/v1/image-jobs', '/api/v1/image-jobs/{job_id}', '/api/v1/image-options']
removed paths  : []
added schemas  : ['ImageCreditCosts', 'ImageJobCreateRequest', 'ImageJobCreatedResponse', 'ImageJobResponse', 'ImageOptionsResponse']
removed schemas: []
changed pre-existing paths  : []
changed pre-existing schemas: []
```
The three routes declare exactly `GET /image-options → 200` (no cookie parameter, public like `/presets`), `POST /image-jobs → 202/401/402/422` and `GET /image-jobs/{job_id} → 200/401/404/422`. The live stub probe against the running `uvicorn --reload` on `:8000`:
```
GET  /api/v1/image-options                                   -> 501 (stub)
POST /api/v1/image-jobs        (no cookie)                   -> 401
POST /api/v1/image-jobs        (guest cookie)                -> 501 (stub)
GET  /api/v1/image-jobs/{uuid} (guest cookie)                -> 501 (stub)
POST /api/v1/image-jobs        (aspect_ratio "2:1")          -> 422
```

## Standards check
```
check-standards: ok (0 violations)
```
New files: `domain/image_rules.py` 28 lines, `schemas/image_jobs.py` 51, `routers/image_jobs.py` 62, `main.py` 67 — all far under 200. `mypy --strict` passes over `app/services`, `app/adapters` **and `app/domain`** (32 files), so `image_rules.py` is fully typed.

## Open issues / guesses / things skipped
- **Backend reality, stated plainly: no real image model exists or can run here.** `ModelAdapter` has only `generate_video`, and D-002's LLaDA-Image Turbo on Modal is blocked on an unverified licence, no GPU deployment and the R2 blocker. The design therefore ships an **`ImageModelAdapter` port + a placeholder PNG backend** and says so in the spec, the design table and AC-10; `modal`/`openrouter` will fail with "image generation is not configured" and refund. Real text→image is **P2** and is one adapter away. **D-014** records this.
- **One migration is unavoidable, so the image path is not a small change.** An image job has no preset and no input image (`job.preset_slug`/`input_asset_id` are `NOT NULL`), `asset.kind` has no `output_image`, and `job` has only two output FKs. `0004` adds an explicit `kind` discriminator, nullable-per-kind video columns, the image params and a `job_image` child table — all additive, with per-kind checks so the video guarantees stay strong.
- **A third route was added on purpose.** The Generate button must show the cost before the POST (AC-4) and the cost depends on user-chosen settings, so `GET /api/v1/image-options` (public) publishes the allowed values and unit costs — the same reasoning as `/presets` for video, and it avoids duplicating money maths in TypeScript.
- **The worker dispatches, not `generation_runs`.** `generation_runs.py` is 181 lines and `image_generation_runs` needs its `renew_lease_until_lost`, so putting the branch there would risk both a 200-line overrun and an import cycle. `worker.py` selects the image adapter and dispatches on `ClaimedStep.kind`; `generation_runs.py` and `step_completion.py` stay **untouched**.
- **The SSE watcher moves to `api/`.** It is already dependency-injected, so it only needs a generic job type; the terminal-status predicate moves to `api/jobStatus.ts` because the watcher is at 197 lines. Specs 004, the future Library work and Create image then share one implementation. This touches three spec-004 files by import path only (the T-005-2/T-006-1 precedent).
- **Two deliberate P1 cuts**, both in the spec: image jobs do **not** appear in the video Library (`GET /jobs` and `GET /jobs/{id}` gain a `kind='video'` filter, AC-11) and images cannot yet be fed into Video create (the product-map reason for P2). Both are testable, not accidental.
- **Cost formula lives in one place** (`domain/image_rules.image_credit_cost`): 10 credits per standard image, 15 per high, aspect-independent; the client only multiplies the server-published units by `count`. Recorded as an open question in case a real model's cost is size/token dependent.
- **Eight tasks is larger than the other P1 packs** because this is a new modality (migration + adapter + worker branch + API + page), not a polish item. The waves keep every parallel pair file-disjoint.
- **`.agent-logs/` for a DSH session is hand-exported** (no automatic exporter covers this harness), in the same format as the committed T-005-0/T-007-0/T-008-0 logs.
- Nothing committed by this report alone — the orchestrator commits the whole T-009-0 change set.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Spec 009 (Create image) designed + contract published: `GET /api/v1/image-options` (public), `POST /api/v1/image-jobs` (202/401/402/422) and `GET /api/v1/image-jobs/{job_id}` as 501 stubs + five image schemas; **no real image model exists** (placeholder PNG backend for `local-motion`/`mock`, D-014), one additive migration `0004` planned; 7 briefs in 4 waves; every pre-existing path/schema byte-identical | `docs/specs/009-image-create/{spec,design,tasks}.md`, `docs/tasks/T-009-{0..7}/brief.md`, `apps/api/app/domain/image_rules.py`, `apps/api/app/schemas/image_jobs.py`, `apps/api/app/routers/image_jobs.py`, `apps/api/app/main.py`, `packages/contracts/openapi.json` | `python3 -c openapi-paths && ls docs/tasks (filter T-009) && scripts/check-standards` → 15 paths incl. the 3 image routes, T-009-0..7 present, 0 violations; contract diff **+451/−0** with 0 pre-existing entries changed; stub live → options 501, no-cookie 401, guest 501, bad enum 422 (full output in `docs/tasks/T-009-0/report.md`) | 2026-09-13 22:58 |
