# Brief T-011-4: Face swap jobs (contract, data, create/read, worker step)

**Role:** implementer (API, money path) · **Depends on:** — (endpoint URL from T-011-3 only for the live check, which the orchestrator does) · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md`.

## Goal
Spec 011 AC-5, the product half. A face-swap job is a new job kind that follows the sequence pattern exactly:
- ledger HOLD at create, SETTLE on success, RELEASE on failure;
- a worker step under the lease;
- SSE, the Library, and the share page.

## Pattern to mirror, line by line
- `schemas/sequence_jobs.py`, `routers/sequence_jobs.py`, `services/sequence_job_creation.py`, `services/sequence_job_views.py`, `repositories/sequence_jobs.py`
- `services/image_generation_runs.py` + `services/image_step_completion.py` (the output goes into `job_image`, position 0)
- `adapters/modal_image_adapter.py` (HTTP adapter style)

## Allowed files
- New: `apps/api/migrations/versions/0008_face_swap.py`, `app/schemas/faceswap_jobs.py`, `app/routers/faceswap_jobs.py`, `app/services/faceswap_job_creation.py`, `app/services/faceswap_job_views.py`, `app/services/faceswap_runs.py`, `app/repositories/faceswap_jobs.py`, `app/adapters/face_swap_adapter.py`, `app/domain/faceswap_rules.py`, `tests/test_faceswap_*.py`
- Edit: `app/models/job.py` (kind + checks), `app/schemas/jobs.py` (`JobKind` adds `"faceswap"`), `app/main.py`, `app/worker.py` (dispatch), `app/settings.py` (`MODAL_FACESWAP_ENDPOINT_URL`), `.env.example`, `app/services/job_views.py` + `library_media.py` (faceswap rows carry `images` like stills), `app/services/share_views.py` (faceswap shares like a still), `packages/contracts/openapi.json` (regenerated), `apps/web/src/api/generated/schema.d.ts` (regenerated)
- `docs/tasks/T-011-4/*`

## The change
1. **Data (`0008`):**
   - Job kind `faceswap`, with nullable `job.face_source_asset_id` and `job.face_target_asset_id` (FKs to asset).
   - Checks: both are set iff kind is faceswap, and preset, aspect, quality and count are NULL.
   - The downgrade reverses it exactly.
2. **Rules (`faceswap_rules.py`):** `FACESWAP_CREDIT_COST = 8`, `FACESWAP_STEP_KIND = "swap_face"`, `FACESWAP_BACKEND = "modal-faceswap"`.
3. **API:**
   - `POST /api/v1/faceswap-jobs {source_asset_id, target_asset_id, idempotency_key}` → 202 `{id, status, credit_cost}`. Both assets must be the user's own and `ready`, with kind `input_image` or `output_image`, otherwise 404. The status codes are 402, 422 (key used by another kind) and 429, all exactly like sequences.
   - `GET /api/v1/faceswap-jobs/{id}` → `{id, status, credit_cost, source_url, target_url, image_url, generated_by, error_message, created_at}`.
4. **Worker:**
   - `swap_face` → `faceswap_runs.run_faceswap_step`: under the lease, call `FaceSwapAdapter.swap(source_url, target_url)` (presigned URLs), which POSTs the Modal endpoint.
   - A 422 from Modal → `GenerationError` carrying the endpoint's `detail` as the user message.
   - Store the PNG as an `output_image` in `job_image` position 0. Then SETTLE, or on failure RELEASE.
   - An empty endpoint setting → `BackendNotConfiguredError` → refund (as other adapters do).
5. **Library and share:** faceswap items show like stills (`images`, `image_urls`, `thumbnail_url`). The share page treats them like a still.
6. **Tests:**
   - create: 202 + a single HOLD, idempotent replay, a foreign asset 404, 402, 429;
   - read;
   - a worker success with a fake adapter writes the image, SETTLE and `generated_by`;
   - a no-face 422 → failed + RELEASE + the message;
   - Library shows `images` for faceswap.

## Acceptance checks
- [ ] Migration up/down/up clean; existing tests green
- [ ] The contract adds only the two paths and the fields above; `JobKind` gains `faceswap`

## Verify command
```
docker compose up -d --wait db minio && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run alembic downgrade 0007 && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && npm --prefix apps/web run gen:api && npm --prefix apps/web run typecheck
```
