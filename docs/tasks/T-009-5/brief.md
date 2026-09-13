# Brief T-009-5: API worker image step — dispatch, run and complete an image job

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/009-image-create/spec.md` (AC-7, AC-8, AC-10)
- Design: `docs/specs/009-image-create/design.md` §§ **Flow 6–7**, **Backend reality**, **Files**
- Existing (read before writing): `apps/api/app/services/generation_runs.py` (`run_claimed_step`, `run_adapter_with_lease`, `renew_lease_until_lost`, `RunSettings`, `GENERIC_FAILURE_MESSAGE`), `apps/api/app/services/step_completion.py` (`complete_step_failure`, `complete_step_success`), `apps/api/app/worker.py` (the claim loop), `apps/api/app/repositories/{job_steps,jobs,ledger,assets}.py`
- Provided by T-009-1: `repositories/image_jobs.py::insert_job_image`/`list_job_images`, the `job.kind`/params model
- Provided by T-009-3: `adapters/image_model_adapter.py`, `adapters/backend_selection.py::select_image_adapter`, `domain/image_rules.py` (`IMAGE_PIXEL_SIZES`)

## Goal
A claimed `generate_image` step produces `count` stored `output_image` assets plus their `job_image` rows, settles the HOLD and completes the job — while the video path stays byte-for-byte unchanged.

## Allowed files (touch nothing else)
- `apps/api/app/services/image_generation_runs.py` (new)
- `apps/api/app/services/image_step_completion.py` (new)
- `apps/api/app/worker.py` (dispatch only)
- `apps/api/tests/test_image_step.py` (new)
- `docs/tasks/T-009-5/report.md`

## Must do
- **`services/image_generation_runs.py`** — `async def run_image_step(session_maker, *, storage, adapter: ImageModelAdapter, claimed: ClaimedStep, worker_id, settings: RunSettings) -> None`, mirroring `run_claimed_step`'s structure exactly:
  1. load the job (`find_job`); if it is missing or not an image job, log and return without touching the step;
  2. `tempfile.TemporaryDirectory(prefix=...)`, build `ImageGenerationRequest(job_id, prompt, aspect_ratio, quality, count, work_dir)`;
  3. run `asyncio.wait_for(adapter.generate_image(request), settings.generation_timeout_seconds)` **racing the lease renewal** the same way `run_adapter_with_lease` does (reuse `renew_lease_until_lost` from `generation_runs`; if the renewal wins, discard the run and return; always cancel both tasks in a `finally`);
  4. upload each result path to `users/{user_id}/jobs/{job_id}/image-{position}.png` (`content_type="image/png"`) and collect `(position, key, byte_size)`;
  5. `complete_image_step_success(...)`.
  - `except GenerationError` → `complete_step_failure(user_message=error.user_message, ...)`; `except Exception` → log + the generic refund message; both exactly like `run_claimed_step`.
  - Do **not** download an input image and do **not** reuse `complete_step_success` (it writes video + poster).
- **`services/image_step_completion.py`** — `async def complete_image_step_success(session_maker, *, step_id, job_id, worker_id, backend, images: list[tuple[int, str, int]]) -> bool`, one transaction mirroring `complete_step_success`:
  1. `finish_step(..., "succeeded", backend=backend)`; if it loses the lease → rollback, return `False`;
  2. load the job; for each `(position, key, size)` `insert_asset(kind="output_image", status="ready", content_type="image/png")` and `insert_job_image(position=position, asset_id=...)`;
  3. `transition_job_status(job_id, "succeeded", allowed_from=statuses_allowed_before("succeeded"), finished_at=...)` — **do not** set the video/poster FKs;
  4. `insert_ledger_entry(kind="SETTLE", amount=0, job_id=...)`, `notify_job_event`, `commit`.
  - Reuse the existing `complete_step_failure` unchanged for failures (it already RELEASEs).
- **`worker.py`** (dispatch only): select the image adapter once (`select_image_adapter(settings)`), log both backend names, and in the loop call `run_image_step(...)` when `claimed.kind == "generate_image"`, else `run_claimed_step(...)`. Keep the loop's existing error handling and reaper untouched; do not edit `generation_runs.py`.
- **Tests** (`test_image_step.py`, ≤200 lines): a fake `ImageModelAdapter` inline (writes tiny files, or reuse `PlaceholderImageAdapter`) — create an image job through the API, claim its step with `claim_step`, run `run_image_step`, then assert:
  - the job is `succeeded`; exactly `count` `output_image` assets exist; `job_image` rows are `(job_id, position)` ordered; no `output_video`/`output_poster` asset was created;
  - the ledger has `HOLD -cost` + `SETTLE 0` and the balance is unchanged after the settle (60 → after HOLD 40 → still 40);
  - with `UnconfiguredImageAdapter`, the job is `failed`, `RELEASE` refunds it (balance back to 60) and `job_step.backend` is recorded;
  - the video path still works: a `generate_video` step is dispatched to `run_claimed_step` and produces video + poster (or assert the dispatch predicate directly, to keep the test small).

## Acceptance checks
- [ ] a claimed image step ends `succeeded` with `count` ready `output_image` assets + `job_image` rows, or `failed` + refunded when the adapter raises
- [ ] the image completion never sets `output_video_asset_id`/`output_poster_asset_id`, and never writes a video/poster asset
- [ ] `generation_runs.py` and `step_completion.py` are **unchanged** (`git diff --name-only` proves it)
- [ ] an unknown step kind does not silently create assets
- [ ] ruff, mypy (strict on `app/services`) and the full suite are green; `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` byte-identical

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards
```
Stop any running `app.worker` first (it would race the test's steps). `test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` is a known pre-existing flake; if it fails, re-run it alone and say so.

## Out of scope
- The API surface/routes (T-009-4) and the adapters (T-009-3) — import them, do not change them.
- `services/generation_runs.py`, `services/step_completion.py`, the schema/router, the migration, any web file.
- Real image models (P2).

## Report
Write `docs/tasks/T-009-5/report.md` using `docs/templates/report.md`. Don't commit; the orchestrator does.
