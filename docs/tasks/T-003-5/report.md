# Report T-003-5

**Agent / model / tool:** implementer (delegated subagent) · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `apps/api/app/worker.py`: replaced the heartbeat loop with the worker loop — engine + `create_session_maker`, `get_object_storage()`, `select_model_adapter(settings)`, `worker_id = f"{hostname}:{pid}:{uuid4().hex[:8]}"`, reaper cadence (`WORKER_REAPER_SECONDS`), claim, poll sleep, `run_claimed_step`, startup/claim/finish log lines, and a catch-all that logs and retries after `WORKER_POLL_SECONDS` (never exits). `main()` stays the entrypoint.
- `apps/api/app/services/step_claiming.py` (new): Flow 2 transaction — claim, transition the job to `running` with `statuses_allowed_before("running")`, `notify_job_event`, commit. A queued step whose job is already terminal is failed without a ledger write so it can never starve the queue (see guesses).
- `apps/api/app/services/generation_runs.py` (new): Flow 3 — load job/preset/input, temp dir per run, `download_to_path`, `GenerationRequest`, lease renewal every `lease_seconds / 5`, `asyncio.wait_for(adapter.generate_video(...), generation_timeout_seconds)`, upload to the deterministic output keys, then Flow 4a/4b. Lease lost → adapter task cancelled, nothing written. `RunSettings` carries the settings values.
- `apps/api/app/services/step_completion.py` (new): Flow 4a (2 ready assets → job `succeeded` → SETTLE 0 → notify) and Flow 4b (job `failed` with the user-safe message → RELEASE `+credit_cost` → notify), one transaction each, guarded by `finish_step` (`allowed_from` from `statuses_allowed_before`).
- `apps/api/app/services/lease_reaper.py` (new): Flow 5 — `lock_expired_steps(limit=20)`, `attempt < MAX_STEP_ATTEMPTS` → `requeue_step` + job `queued`, else `fail_step` + job `failed` with `"Generation timed out. Your credits were refunded."` + RELEASE, one commit per batch.
- `apps/api/tests/fakes/scripted_model_adapter.py` (new): `ModelAdapter` double with `success` / `generation_error` / `runtime_error` / `hang` outcomes.
- `apps/api/tests/test_step_claiming.py` (new): service-level double-claim (1 winner, job `running`, NOTIFY observed on a real LISTEN connection), empty queue → `None`, terminal-job step abandoned without blocking the next claim.
- `apps/api/tests/test_step_completion.py` (new): success (2 ready assets at `users/{user}/jobs/{job}/video.mp4` and `poster.jpg`, one SETTLE 0, balance 40), `GenerationError("Nope")` → job `failed`, `error_message == "Nope"`, RELEASE +20, balance 60, `RuntimeError`/timeout → generic message (never the exception text), lost lease → no SETTLE/RELEASE and no job/output change.
- `apps/api/tests/test_lease_reaper.py` (new): first expiry re-queues (attempt stays 1, job `queued`, no RELEASE), second expiry fails (attempt 2, timeout copy, RELEASE +20, balance 60), live lease left alone.
- `docs/tasks/T-003-5/report.md`: this file.

No file outside the brief's Allowed list was touched.

## Reused
- `app/repositories/job_steps.py` (`claim_next_queued_step`, `renew_step_lease`, `finish_step`, `lock_expired_steps`, `requeue_step`, `fail_step`), `repositories/jobs.py` (`find_job`, `read_job_status`, `transition_job_status`, `notify_job_event`), `repositories/assets.py` (`insert_asset`, `find_user_asset`, `find_assets_by_ids`), `repositories/ledger.py` (`insert_ledger_entry`).
- `app/domain/job_states.py` (`TERMINAL_STATUSES`, `statuses_allowed_before`), `app/domain/credit_rules.py` (`MAX_STEP_ATTEMPTS`, `release_amount`).
- `app/adapters/model_adapter.py` types, `app/adapters/object_storage.py::ObjectStorage`, `app/adapters/backend_selection.py::select_model_adapter`, `app/storage_dependencies.py::get_object_storage`.
- `app/db.py::create_database_engine` / `create_session_maker`; conftest fixtures (`session_maker`, `object_storage`, `guest_client`), `tests/job_api_helpers.py`, `tests/job_event_helpers.py` (`open_broker`, `wait_for_wake_up`), `tests/fakes/in_memory_object_storage.py`.

## Verify output (full paste, no summarising)
```
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
All checks passed!
Success: no issues found in 29 source files
........................................................................ [ 66%]
....................................                                     [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
108 passed, 2 warnings in 39.10s
2026-09-13 08:47:23,933 worker worker fedora:244059:4b16a7e5 backend=mock lease=300s poll=1.0s
2026-09-13 08:47:23,980 worker claimed step e41c72da-d096-4dbc-9acc-cb896e697544 job=7992cf65-7c7c-4df8-ab4b-81b3d577a653 attempt=2
2026-09-13 08:47:23,996 app.services.generation_runs generation failed for step e41c72da-d096-4dbc-9acc-cb896e697544
Traceback (most recent call last):
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/app/services/generation_runs.py", line 60, in run_claimed_step
    result = await run_adapter_with_lease(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/app/services/generation_runs.py", line 94, in run_adapter_with_lease
    await storage.download_to_path(inputs.input_key, input_path)
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/app/adapters/s3_object_storage.py", line 51, in download_to_path
    await asyncio.to_thread(self._client.download_file, self._bucket, key, str(path))
  File "/home/deepjyoti/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/lib/python3.12/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/lib/python3.12/concurrent/futures/thread.py", line 59, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/botocore/context.py", line 123, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/boto3/s3/inject.py", line 223, in download_file
    return transfer.download_file(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/boto3/s3/transfer.py", line 484, in download_file
    future.result()
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/s3transfer/futures.py", line 111, in result
    return self._coordinator.result()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/s3transfer/futures.py", line 287, in result
    raise self._exception
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/s3transfer/tasks.py", line 272, in _main
    self._submit(transfer_future=transfer_future, **kwargs)
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/s3transfer/download.py", line 379, in _submit
    response = client.head_object(
               ^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/botocore/client.py", line 606, in _api_call
    return self._make_api_call(operation_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/botocore/context.py", line 123, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/botocore/client.py", line 1094, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.exceptions.ClientError: An error occurred (404) when calling the HeadObject operation: Not Found
2026-09-13 08:47:24,012 worker finished step e41c72da-d096-4dbc-9acc-cb896e697544
worker ran 6s
check-standards: ok (0 violations)
```

Note: the traceback in the worker section is expected, not a failure. The worker claimed a step left
over by the test suite; its input image exists only in the tests' `InMemoryObjectStorage`, so the real
MinIO/S3 backend returned 404, the worker released the hold, logged it, and kept looping. `timeout`
killed the process at 6s (exit 124), which is the acceptance check.

## Standards check
```
check-standards: ok (0 violations)
```
(`scripts/check-standards` was also run by the verify command above and printed the same line.)

## Open issues / guesses / things skipped
- **Liveness gap in the design (guess):** Flow 2 says to call `transition_job_status(job, 'running', allowed_from={'queued'})` without saying what to do when the job is not queued. The first verify run showed the consequence: a `queued` step whose job was already terminal was claimed, rolled back, and re-claimed forever — the worker never reached any later queued step (queue starvation). `claim_step` now reads the job status and, when it is terminal, rolls the claim back and fails the step (`last_error="job already terminal"`, no ledger write, no notify) so the queue keeps moving. When the job is already `running` (the lost-lease re-queue case) the claim is accepted and the transition is a no-op, matching the design's unchecked call. A reviewer should confirm failing such a step is the intended disposition.
- **NOTIFY assertion:** the double-claim test listens on a real `job_events` LISTEN connection through the existing `JobEventBroker` helper (stronger than the brief's permitted `read_job_status` fallback).
- **Leftover test rows are not cleaned up** (same as the existing job API tests): tests drain the queue first, but the shared dev DB keeps the guests/jobs they create. Two drained `running` steps with live 300s leases are left behind after each full pytest run; the reaper disposes of them later.
- **Helper duplication in tests (forced):** `drain_queued_steps` and the small snapshot readers are duplicated across the three new test files because `tests/job_api_helpers.py` is outside the Allowed files.
- **`fail_step` keeps `lease_owner`** (T-003-2 SQL clears it only on `requeue_step`); `test_lease_reaper` asserts the owner is still the worker after the second expiry. Matches the repository, may be worth a look if `lease_owner` is meant to mean "currently held".
- **Capture/commit:** this ran as a delegated DSH subagent, not through `scripts/agent-run`; the orchestrator owns `.agent-logs/` and the commit (no commit was made here).

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Worker: claim/lease, run + renew, settle/release completion, reaper re-queue then refund | `apps/api/app/worker.py`, `apps/api/app/services/{step_claiming,generation_runs,step_completion,lease_reaper}.py` | `uv --directory apps/api run pytest -q` (108 passed) + `GENERATION_BACKEND=mock timeout 6 uv run python -m app.worker` (ran 6s) | 2026-09-13 08:47 |
