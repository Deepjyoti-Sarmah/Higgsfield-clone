# Report T-011-4

**Agent:** sonnet-5@claude-code · **Role:** implementer (API, money path) · **Result:** DONE

## Files changed
- `apps/api/migrations/versions/0008_face_swap.py`: new `faceswap` job kind, `face_source_asset_id` /
  `face_target_asset_id` FKs to asset, and the check constraints (kind, inputs-by-kind, image-params,
  faceswap-assets). Downgrade reverses all of it.
- `apps/api/app/models/job.py`: added the two FK columns and extended `JOB_KIND_CHECK`,
  `JOB_INPUTS_BY_KIND_CHECK`, `JOB_IMAGE_PARAMS_CHECK`, plus the new `JOB_FACESWAP_ASSETS_CHECK`.
- `apps/api/app/domain/faceswap_rules.py` (new): `FACESWAP_CREDIT_COST=8`, `FACESWAP_STEP_KIND="swap_face"`,
  `FACESWAP_BACKEND="modal-faceswap"`.
- `apps/api/app/schemas/faceswap_jobs.py` (new): create request/response + read response.
- `apps/api/app/schemas/jobs.py`: `JobKind` gains `"faceswap"`.
- `apps/api/app/repositories/faceswap_jobs.py` (new): insert + owned-find.
- `apps/api/app/services/faceswap_job_creation.py` (new): mirrors `sequence_job_creation.py` /
  `image_job_creation.py` — lock, idempotency replay, `enforce_creation_limits`, asset ownership +
  kind/status checks (reuses `job_creation.INPUT_ASSET_KINDS`), balance check, HOLD, commit with the
  race-on-idempotency-key handling.
- `apps/api/app/services/faceswap_job_views.py` (new): read-owned view; resolves source/target/image URLs.
- `apps/api/app/adapters/face_swap_adapter.py` (new): HTTP adapter mirroring `modal_image_adapter.py`.
  POST `{source_url, target_url}`, bearer auth; success is `{image_base64, width, height}`; a 422 response's
  `{detail}` is surfaced verbatim as the `GenerationError` user message. Confirmed against T-011-3's brief
  by the orchestrator — matches exactly.
- `apps/api/app/services/faceswap_runs.py` (new): worker step mirroring `image_generation_runs.py` —
  presigned download URLs (no local download needed), lease renewal race, uploads the PNG, stores it via
  `complete_image_step_success` at `job_image` position 0, or refunds via `complete_step_failure`.
- `apps/api/app/routers/faceswap_jobs.py` (new): `POST /api/v1/faceswap-jobs`, `GET /api/v1/faceswap-jobs/{id}`,
  same status-code mapping as sequences (404/402/422/429).
- `apps/api/app/main.py`: registered `faceswap_jobs.router`.
- `apps/api/app/worker.py`: added `face_swap_adapter` (optional kw, defaults to a fresh `FaceSwapAdapter`)
  and dispatch on `FACESWAP_STEP_KIND`; `run_worker_loop` builds and passes a real `FaceSwapAdapter`.
- `apps/api/app/settings.py`, `.env.example`: `MODAL_FACESWAP_ENDPOINT_URL`.
- `apps/api/app/services/library_media.py`: new `STILL_LIKE_KINDS = ("image", "faceswap")`, used in
  `find_images_by_job`.
- `apps/api/app/services/job_views.py`, `apps/api/app/services/share_views.py`: switched their
  `kind == "image"` checks to `kind in STILL_LIKE_KINDS` so faceswap rows carry `images`/`image_urls` like
  stills, in the Library and on the share page.
- `packages/contracts/openapi.json`, `apps/web/src/api/generated/schema.d.ts`: regenerated. Diff adds only
  the two `faceswap-jobs` paths and `faceswap` in `JobKind` — nothing else moved.
- **Web, approved by the orchestrator after the widened contract broke typecheck (out of this brief's
  original allowed-files list, approved out-of-band):**
  - `apps/web/src/features/share/shareCopy.ts`: `shareTitle`/`shareMeta` now take
    `JobKind = components["schemas"]["PublicJobResponse"]["kind"]` (imported from the generated schema,
    per the orchestrator's preference) instead of a hand-written union; both treat `"faceswap"` like
    `"image"` (a still).
  - `apps/web/src/features/share/ShareResult.tsx`: the video/image-grid branch now routes `"faceswap"`
    through the still (image) path too.
  - `apps/web/src/features/studio/StudioStage.tsx`: added a small `badgeKind()` helper mapping
    `"faceswap" -> "image"` for the two call sites (`GenerationBadge`, `StageProgress`) whose prop types
    predate faceswap; `TerminalMedia`'s existing `kind === "video" || kind === "sequence"` branch already
    routed anything else (now including faceswap) through the still/image-grid rendering, unchanged.
- Tests (new): `tests/test_faceswap_jobs_api.py`, `tests/test_faceswap_step.py`, `tests/test_faceswap_library.py`.

## Reused
- `app.services.job_creation.INPUT_ASSET_KINDS` and `enforce_creation_limits` (not edited).
- `app.services.image_job_creation.IdempotencyKeyConflictError` (not edited).
- `app.services.image_step_completion.complete_image_step_success` and
  `app.services.step_completion.complete_step_failure` (not edited) for SETTLE/RELEASE + `job_image`.
- `app.services.adapter_runs.renew_lease_until_lost` for the lease race during the adapter call.

## Verify: see `verify.log`
```
271 passed, 3 warnings in 62.76s (0:01:02)
wrote packages/contracts/openapi.json
openapi-typescript ... schema.d.ts [83ms]
tsc -b   (clean, no errors)
check-standards: ok (0 violations)
RESULT: PASS
```
ruff, mypy, alembic upgrade/downgrade/upgrade, pytest, openapi export, web codegen, web typecheck and
check-standards all pass.

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **Resolved blocker:** widening `JobKind` to include `"faceswap"` broke `npm run typecheck` in three web
  files that hardcoded `"video" | "image" | "sequence"` instead of deriving the type from the schema. Flagged
  via `scripts/task say T-011-4 QUESTION`; the orchestrator approved minimal, out-of-brief edits to exactly
  those three files (see Files changed above), confirmed the Modal wire format matches T-011-3's brief, and
  asked for verify to be re-run to PASS before submitting. Done.
- `GenerationBadge` and `StageProgress` (in `apps/web/src/ui/GenerationBadge.tsx` and
  `apps/web/src/features/studio/StageProgress.tsx`) still don't know about `"faceswap"` natively — I mapped
  it to `"image"` at the call sites in `StudioStage.tsx` rather than widen those two components' own prop
  types, since the orchestrator's approval named only the three files above and this keeps the edit minimal.
  One real consequence: `StageProgress` polls `/api/v1/image-jobs/{id}` for a faceswap job that's still
  queued/running (not `/api/v1/faceswap-jobs/{id}`), so live progress for an in-flight faceswap job won't
  resolve via that path — the label/copy is otherwise correct (rendered as a still). Wiring a proper
  faceswap progress path in `apps/web/src/api/jobProgress.ts` is UI work that belongs with T-011-5 ("face
  swap tab, web"), which is the next wave in `docs/specs/011-quality-faceswap-trim/tasks.md`.
- Faceswap job creation does not treat `modal-faceswap` as a paid backend for budget purposes (same
  treatment as `sequence`/`stitch_video`, which use `ffmpeg`); the brief doesn't ask for paid-budget
  enforcement on this job kind and none of the sibling job kinds outside `image`/`video` do either.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Face swap jobs (API: create/read, ledger HOLD/SETTLE/RELEASE, worker step, Library+share as a still) | `apps/api/app/{routers,services,repositories,adapters,domain}/*faceswap*`, migration `0008_face_swap`, minimal web kind-union widening in `shareCopy.ts`/`ShareResult.tsx`/`StudioStage.tsx` | `docs/tasks/T-011-4/verify.log` (RESULT: PASS — 271 pytest, ruff, mypy, alembic up/down/up, web typecheck, check-standards) | 2026-09-26 |
