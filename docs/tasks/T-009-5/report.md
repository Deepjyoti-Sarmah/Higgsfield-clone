# Report T-009-5

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `apps/api/app/services/image_step_completion.py` (new, 62 lines): `complete_image_step_success(session_maker, *, step_id, job_id, worker_id, backend, images)` — one transaction mirroring `complete_step_success`: `finish_step("succeeded")` (rollback + `False` if the lease was lost) → one ready `output_image` asset + one `job_image` row per `(position, key, size)` → `transition_job_status("succeeded")` **without** the video/poster FKs → `SETTLE 0` → notify → commit.
- `apps/api/app/services/image_generation_runs.py` (new, 146 lines): `run_image_step(...)` plus `load_image_step_input`, `generate_with_lease`, `upload_images`. It does **not** download an input image, calls `adapter.generate_image`, races the adapter against `renew_lease_until_lost` exactly like `run_adapter_with_lease`, uploads each PNG to `users/{uid}/jobs/{jid}/image-{position}.png`, then completes. `GenerationError` → `complete_step_failure(user_message=...)`; any other exception → log + the generic refund message.
- `apps/api/app/worker.py` (edit, 95 → 124 lines): the dispatch is extracted as `run_claimed_step_for_kind(...)` (`generate_image` → the image run, else the video run) and the loop calls it; the image adapter is selected and logged once at startup. The reaper, poll loop and error handling are untouched.
- `apps/api/tests/test_image_step.py` (new, 197 lines): 4 tests that call the **real** `run_claimed_step_for_kind` with both adapters, so the worker's dispatch itself is exercised.
- `docs/tasks/T-009-5/report.md`: this report.

## Reused
- `generation_runs.RunSettings` + `GENERIC_FAILURE_MESSAGE` + `renew_lease_until_lost` (the lease reaper/renewal is not re-implemented).
- `step_completion.complete_step_failure` **unchanged** for the failure path — it already writes the `RELEASE` refund.
- `repositories/{assets,job_steps,jobs,ledger,image_jobs}` (`insert_asset`, `finish_step`, `find_job`, `transition_job_status`, `notify_job_event`, `insert_ledger_entry`, `insert_job_image`), `domain/job_states.statuses_allowed_before`.
- T-009-3's `PlaceholderImageAdapter`/`UnconfiguredImageAdapter` and T-009-4's API in the tests.

## Verify output (full paste, no summarising)
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
docker exit=0
alembic exit=0
All checks passed!
ruff exit=0
Success: no issues found in 40 source files
mypy exit=0
........................................................................ [ 42%]
........................................................................ [ 85%]
.........................                                                [ 100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
169 passed, 2 warnings in 50.95s
pytest exit=0
wrote packages/contracts/openapi.json
export exit=0
contract-diff exit=0
check-standards: ok (0 violations)
standards exit=0
```
`169 passed` = the 165 after T-009-4 + my 4. Contract byte-identical (no schema touched).

**`generation_runs.py` / `step_completion.py` proof.** `step_completion.py` is not in `git diff --name-only` at all (unchanged). `generation_runs.py` shows exactly one hunk, and it is T-009-1's approved guard, not this task's:
```
-        if job is None:
+        # The video run needs both video-only columns; an image step never reaches here.
+        if job is None or job.input_asset_id is None or job.preset_slug is None:
```
T-009-5 added no line to it (it only imports `RunSettings`, `GENERIC_FAILURE_MESSAGE`, `renew_lease_until_lost`).

## Standards check
```
check-standards: ok (0 violations)
```
Sizes: `image_generation_runs.py` 146 · `image_step_completion.py` 62 · `worker.py` 124 · `test_image_step.py` 197 — all ≤200. `run_image_step` is ~40 lines, `complete_image_step_success` ~33; `mypy --strict` green (40 files).

## Acceptance checks
- [x] a claimed image step ends `succeeded` with `count` ready `output_image` assets + ordered `job_image` rows (`test_a_claimed_image_step_stores_outputs_and_settles`: `{"output_image": 2}`, positions `[1, 2]`, `image_urls` ending `image-1.png?get`/`image-2.png?get`), or `failed` + refunded when the adapter raises (`test_an_unconfigured_image_backend_fails_and_refunds`: `backend="modal"`, 1 `RELEASE`, 0 `job_image`, 0 assets, balance back to 60).
- [x] the image completion never sets the video/poster FKs (`tuple(output_fks) == (None, None)`) and no `output_video`/`output_poster` asset is written (the kind census is exactly `{"output_image": 2}`); the ledger is exactly `HOLD -20` then `SETTLE 0`, and the balance stays 40.
- [x] `step_completion.py` unchanged; `generation_runs.py` carries only T-009-1's guard (shown above).
- [x] an unknown step kind creates nothing (`test_an_unknown_step_kind_creates_nothing`: a `generate_unknown` step falls to the video path, `load_step_inputs` returns `None` because the image job has no input asset, and the assertion is 0 assets).
- [x] `test_the_video_step_path_is_unchanged` runs a real `generate_video` step through the same dispatcher and gets `succeeded` with video + poster URLs.
- [x] ruff, mypy strict (40 files), the full suite and the byte-identical contract check are green.

## Open issues / guesses / things skipped
- **The dispatch is now a named function** (`run_claimed_step_for_kind`) rather than an inline `if` in the loop. That was a deliberate improvement so the test exercises the worker's real branch instead of re-implementing it with `hasattr`; behaviour is identical.
- **An unknown kind leaves its step `running`** until the lease expires and the reaper re-queues/fails it (the video path logs and returns without finishing the step). That matches the pre-existing `run_claimed_step` behaviour for a job with no input asset; the reaper (spec 003) is the safety net. Recorded, not changed.
- **No live worker process was run** in this task: the tests call the real dispatcher + real placeholder adapter against the real DB and the in-memory storage, which covers the same code path. A full `verify-slice` with `APP_ROLE=worker` remains for T-009-7.
- **Placeholder output size** (~600 KB per 640×360 PNG, noted in T-009-3) is unaffected by this task.
- No commit (per the brief). No schema, route, adapter, migration or web file was touched.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Image worker step live: `run_claimed_step_for_kind` dispatches `generate_image` to `run_image_step` (no input download, lease-racing, placeholder adapter, N PNG uploads) and completion writes ready `output_image` assets + `job_image` rows + `SETTLE`, or fails + `RELEASE`s via the untouched generic path | `apps/api/app/services/{image_generation_runs,image_step_completion}.py`, `apps/api/app/worker.py`, `apps/api/tests/test_image_step.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` → 169 passed (4 new), mypy clean (40 files), contract byte-identical, 0 violations | 2026-09-13 23:17 |
