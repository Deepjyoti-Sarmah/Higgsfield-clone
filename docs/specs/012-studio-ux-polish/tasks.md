# Tasks 012-T6: video-target face swap (4 disjoint implementer briefs)

Order: T6a → (T6b, T6c in parallel once T6a's schemas exist) → T6d. No brief touches another
brief's files. None modifies the 011 image path except the listed additive branches.

## T6a — Contract + data (API)

**Goal:** migration 0010, domain/schemes/repos, creation + read services, router, regenerated
contract. No GPU, no worker run logic, no web.
**Allowed files:** `apps/api/migrations/versions/0010_video_faceswap.py`, `apps/api/app/models/job.py`,
`apps/api/app/domain/video_faceswap_rules.py` (new), `apps/api/app/schemas/video_faceswap_jobs.py`
(new), `apps/api/app/schemas/jobs.py`, `apps/api/app/repositories/video_faceswap_jobs.py` (new),
`apps/api/app/services/video_faceswap_job_creation.py` (new),
`apps/api/app/services/video_faceswap_job_views.py` (new),
`apps/api/app/routers/video_faceswap_jobs.py` (new), `apps/api/app/main.py`,
`apps/api/app/services/job_views.py`, `apps/api/app/services/share_views.py`,
`apps/api/app/settings.py`, `.env.example`, `packages/contracts/openapi.json`,
`apps/web/src/api/generated/schema.d.ts`, `apps/api/tests/test_video_faceswap_jobs_api.py` (new).
**Key rules:** mirror `faceswap_job_creation.py` (lock → idempotency → limits → assets → balance →
job + `swap_face_video` step + HOLD → notify); source must be ready `input_image`/`output_image`,
target ready `output_video` with mp4/≤30 s/≤50 MB metadata (else 422, no HOLD); cost
`ceil(duration_s) × 2` via `video_faceswap_cost`; openapi diff must show only the two new paths +
`JobKind`. If the `JobKind` widening breaks web typecheck, report it, do not fix (T6c owns web).
**Verify:**
`uv --directory apps/api run alembic upgrade head && uv --directory apps/api run alembic downgrade -1 && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --stat packages/contracts/openapi.json && scripts/check-standards` → all green, RESULT: PASS in `report.md`.

## T6b — GPU + worker (Modal + adapter + step)

**Goal:** `swap_video` on Modal, the HTTP adapter, and the worker step dispatch. Needs T6a's
`video_faceswap_rules.py` + migration applied; nothing else from T6a.
**Allowed files:** `apps/gpu/video_face_swap.py` (new), `apps/gpu/tests/test_video_faceswap_core.py`
(new), `apps/api/app/adapters/video_face_swap_adapter.py` (new),
`apps/api/app/services/video_faceswap_runs.py` (new), `apps/api/app/worker.py`,
`apps/api/tests/test_video_faceswap_step.py` (new).
**Key rules:** reuse `face_swap_core` per-frame math and the `face-swap-weights` Volume (no new
weights, no new secrets besides the endpoint URL already added by T6a); ≤ 10 fps / 300-frame cap;
audio `-c:a copy`; > 50% faceless frames → `NoFaceError` → HTTP 422 `detail`; adapter surfaces the
422 detail verbatim as `GenerationError` (refund message); worker re-verifies duration/streams with
ffprobe before upload; `GENERATION_BACKEND=mock` in tests (never call paid Modal from pytest).
Record cold/warm timings and GPU type in `report.md`.
**Verify:**
`uv run --with numpy --with pytest pytest apps/gpu/tests/test_video_faceswap_core.py && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && GENERATION_BACKEND=mock uv --directory apps/api run pytest -q tests/test_video_faceswap_step.py && scripts/check-standards` → all green, RESULT: PASS in `report.md`, plus one real paid `swap_video.remote` probe logged with cost (or BLOCKED with the exact error).

## T6c — Web UI (Face swap tab video target)

**Goal:** video-target toggle, rail/upoad video well, keyframe preview via the existing image
submit, per-second render action, rail/stage/share/add-to-sequence wiring.
**Allowed files:** `apps/web/src/api/videoFaceswapJobs.ts` (new, +test),
`apps/web/src/api/jobProgress.ts`, `apps/web/src/features/studio/StudioStage.tsx`,
`apps/web/src/features/studio/StageActions.tsx`, `apps/web/src/features/studio/StudioPage.tsx`,
`apps/web/src/features/face-swap/*` (video-well + preview + cost files only, no edits to the
image submit path), `apps/web/src/features/studio/railItemTitle.ts`,
`apps/web/src/features/share/ShareResult.tsx`, `apps/web/src/features/share/shareCopy.ts`,
`apps/web/src/api/generated/schema.d.ts` (regen only).
**Key rules:** preview = existing `submitFaceSwap` on the extracted keyframe (8 credits, unchanged
code); render button shows `ceil(duration_s) × 2` + the separate preview cost; never import another
feature's internals (shared bits go to `ui/` or `api/`); one component per file, Tailwind utilities
only; fix any T6a `JobKind`-widening typecheck breaks minimally inside the allowed list.
**Verify:**
`npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` → all green, RESULT: PASS in `report.md`, plus local screenshots of preview → render → rail entry.

## T6d — End-to-end verify (live + ledger)

**Goal:** prove AC-1…AC-7 on a deployed stack; no product code changes (test/script files only).
**Allowed files:** `docs/verification/T6-video-faceswap/*` (screenshots, ffprobe logs, ledger
dumps), `docs/tasks/T-012-T6d/report.md`.
**Key rules:** guest → upload photo + ≤30 s mp4 → keyframe preview (8 HOLD→SETTLE) → render
(HOLD = `ceil(s) × 2`, ledger shows HOLD then SETTLE 0) → ffprobe output vs target (size/fps/
duration match, audio stream identical codec) → rail + stage + share playback → add-to-sequence;
then the three error cases: faceless source photo → refund + message; > 30 s upload → 422 with no
HOLD row; insufficient balance → 402 `{detail, balance, required}`. Never run paid generation in
loops; one paid render maximum, cost recorded.
**Verify:** `scripts/smoke-sequence`-style run (or the manual equivalent with `curl` + ledger
queries) pasted in full in `report.md`: each AC maps to a check with PASS/FAIL, RESULT: PASS only
if all seven pass, `scripts/check-standards` ok.
