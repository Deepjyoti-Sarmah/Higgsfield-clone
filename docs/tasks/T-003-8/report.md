# Report T-003-8

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## The flake, reproduced and explained
`test_first_expiry_requeues_then_second_fails_and_refunds` went red in full-suite runs because the shared dev DB carries **non-terminal leftovers from earlier test runs**. The chain, confirmed by reading the code and by reproducing it:

1. Several test files claim queued steps and never finish them (`tests/test_step_claiming.py`, `tests/test_step_completion.py`, and `test_lease_reaper.py`'s own second test). A claim sets `status='running'` with a **300 s** lease (`LEASE_SECONDS`).
2. Those rows stay `running` forever. After the suite ends, 300 s later, their leases are expired.
3. The next full-suite run reaches the reaper test, whose guards only drain steps that are **queued** (`drain_queued_steps`). A `running`-with-expired-lease leftover is invisible to it.
4. The test's `reap_expired_steps(...)` is **global**, so it re-queues those leftovers too (attempt 1 → 2).
5. The test's second `claim_step` is FIFO (`CLAIM_STEP_SQL` orders `created_at` ascending), so it picks the **oldest queued** row — a leftover, not the test's own step → `assert second.job_id == job_id` fails with `attempt=2`.

That also explains the "red first, green immediately after" pattern: a run that starts within 5 minutes of the previous one still has *live* leftover leases, so nothing is re-queued and the test passes; once they expire, it goes red. (`tests/test_job_step_repository.py` also writes expired leases at lines 172–173, but it has an autouse `remove_created_rows` fixture that deletes its rows, so it is not a contributor — verified by running that file before the reaper test, which passed.)

**Reproduction** (deterministic, no code change needed): expire the accumulated `running` leftovers, which is exactly the state after any >5 min gap, then run the single test:
```
$ docker exec ... psql -c "UPDATE job_step SET lease_expires_at = now() - interval '1 minute' WHERE status = 'running';"
UPDATE 15
$ uv --directory apps/api run pytest -q "tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds"
...
    second = await claim_step(session_maker, WORKER_ID, LEASE_SECONDS)
>   assert second is not None and second.job_id == job_id
E   AssertionError: assert (ClaimedStep(id=UUID('bf6eb015-...'), job_id=UUID('6c8e8634-...'), kind='generate_video', attempt=2) ...
E        where UUID('6c8e8634-...') = ....job_id
tests/test_lease_reaper.py:103: AssertionError
1 failed in 0.82s
```
The same failure shape the brief describes: the second claim returns a different job's step with `attempt=2`.

## Files changed
- `apps/api/tests/test_lease_reaper.py` (edit, 140 → 139 lines): replaced the `drain_queued_steps` helper (which only drained **queued** rows) with `clear_reapable_steps`, which deletes the rows the global claim/reaper can actually pick:
  ```python
  async def clear_reapable_steps(session_maker: async_sessionmaker[AsyncSession]) -> None:
      """Delete non-terminal leftovers the global claim/reaper could pick instead of this test's.

      Ledger/job/asset rows are kept: the assertions below read this guest's ledger balance.
      """
      async with session_maker() as session:
          await session.execute(text("DELETE FROM job_step WHERE status IN ('queued', 'running')"))
          await session.commit()
  ```
  Both tests now call it before creating their job. `drain_queued_steps`, its `DRAIN_WORKER` constant and the now-unused `claim_next_queued_step` import were removed (nothing imports them — checked with grep across `apps/api/tests/`).
  - **Every assertion in both tests is unchanged**, including the `RELEASE`-absent-on-first-pass and the `RELEASE`-present-plus-refund-on-second-pass pair.
  - Terminal rows (`succeeded`/`failed`) are deliberately left alone: they can never be claimed or reaped. `ledger_entry`/`job`/`asset` are deliberately **not** touched, so the guest's balance assertions still read a real ledger.
- `docs/tasks/T-003-8/report.md`: this report.
- **`apps/api/tests/conftest.py` was not needed** (preferred fix #1 is test-local); `apps/api/app/**` is **untouched** (`git status --short -- apps/api/app` is empty).

## Fix verified against the same leftover state
```
$ docker exec ... psql -tAc "SELECT status, count(*) FROM job_step WHERE status IN ('queued','running') GROUP BY status;"
queued|14
running|1
$ uv --directory apps/api run pytest -q "tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds"
1 passed in 0.99s
$ uv --directory apps/api run pytest -q tests/test_lease_reaper.py
2 passed in 0.94s
```
15 non-terminal leftovers were present, and the test still claimed its own step.

## The test still detects a broken reaper
I temporarily changed the requeue branch to `if step.attempt < 0:` (a one-token local break), ran the test, then restored the file from a backup:
```
$ uv --directory apps/api run pytest -q "...::test_first_expiry_requeues_then_second_fails_and_refunds"
>   assert await step_snapshot(session_maker, first.id) == ("queued", 1, None, FIRST_EXPIRY_ERROR)
E   AssertionError: assert ('failed', 1, ...xpired twice') == ('queued', 1, ...ease expired')
1 failed in 0.87s
--- restoring ---
$ git diff --exit-code apps/api/app/services/lease_reaper.py
apps/api/app/services/lease_reaper.py: identical to HEAD (no production change)
$ uv --directory apps/api run pytest -q tests/test_lease_reaper.py
2 passed in 1.13s
```
So the first-expiry re-queue assertion is the one that fires when the reaper stops doing its job — the test was not made vacuous by the cleanup.

## Verify output (full paste, no summarising)
To make both full runs genuinely exercise the old failure path, I expired the accumulated `running` leftovers **before each run** (that is the real-world state after a >5 min gap); the second run therefore started with 11 expired leftovers.
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
--- expire leftovers before FULL RUN 1 ---
UPDATE 1
expired running leftovers: 1
........................................................................ [ 42%]
........................................................................ [ 84%]
...........................                                              [ 100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
171 passed, 2 warnings in 47.88s
pytest run1 exit=0
--- expire leftovers before FULL RUN 2 ---
expired running leftovers: 11
........................................................................ [ 42%]
........................................................................ [ 84%]
...........................                                              [ 100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
171 passed, 2 warnings in 48.78s
pytest run2 exit=0
--- ordering run ---
................                                                         [ 100%]
16 passed in 3.16s
pytest ordering exit=0
check-standards: ok (0 violations)
standards exit=0
```
Before the fix, the same "expired leftovers" state produced the red run shown at the top; after it, two consecutive full runs and the ordering run are green. A worker was checked first — none running.

## Standards check
```
check-standards: ok (0 violations)
```
`test_lease_reaper.py` = 139 lines (was 140); `clear_reapable_steps` is 6 lines. `mypy --strict` green (40 files) and `ruff check .` clean.

## Acceptance checks
- [x] **two consecutive full-suite runs green** (171 passed each, with expired leftovers seeded before each — the second starting from 11 expired leftovers).
- [x] `pytest -q tests/test_lease_reaper.py` green on its own (`2 passed`).
- [x] the ordering run `tests/test_job_creation_api.py tests/test_library_api.py tests/test_lease_reaper.py` → **16 passed**, so ordering no longer matters.
- [x] the test still fails when the reaper is broken (shown above, then reverted; `git diff --exit-code` clean).
- [x] no production change: `apps/api/app/**` untouched.
- [x] `scripts/check-standards` passes; no file over 200 lines.
- [x] **For the orchestrator's docs sync:** the `STATUS.md` § BROKEN row "`test_first_expiry_requeues_then_second_fails_and_refunds` fails in the full suite but passes alone…" can now be **removed**, and the older entry about `test_migrations.py`'s downgrade is unrelated. `WORKLOG.md` should get a T-003-8 line.

## Open issues / guesses / things skipped
- **Scope of the cleanup.** `clear_reapable_steps` deletes **all** non-terminal `job_step` rows, not just this test's — that is what the brief's preferred fix #1 asks for ("so the only steps the global reaper can touch are this test's"). It is safe here because tests never share jobs across files, and it was proven by the full suite + ordering run. It intentionally leaves `ledger_entry`/`job`/`asset` rows alone so the guest's balance assertions stay meaningful.
- **The root cause is the shared dev DB, not the reaper.** A per-test database or a transactional-rollback harness would remove this whole class of coupling (the brief lists it as out of scope; I agree it is the only fully correct long-term fix, and it is a bigger change than this task allows).
- **Other files still leave running leftovers** (`test_step_claiming.py`, `test_step_completion.py`, and `test_lease_reaper.py`'s second test). They no longer affect the reaper test, but they are why the DB accumulates `running` rows; a future flake of the same shape elsewhere would point at them.
- No commit (per the brief) and no docs sync (STATUS/WORKLOG/PLAN) — the orchestrator owns those; the STATUS row removal is called out above.
- `.agent-logs/` was not written for this task (DSH harness without auto-capture), consistent with the note in `docs/STATUS.md`.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Lease-reaper test isolation: `clear_reapable_steps` deletes the non-terminal `job_step` leftovers the global claim/reaper could pick, in place of the queued-only `drain_queued_steps`, so `test_first_expiry_requeues_then_second_fails_and_refunds` no longer depends on what earlier tests/runs left in the shared DB; every assertion unchanged | `apps/api/tests/test_lease_reaper.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && uv --directory apps/api run pytest -q && uv --directory apps/api run pytest -q tests/test_job_creation_api.py tests/test_library_api.py tests/test_lease_reaper.py && scripts/check-standards` → 171 + 171 + 16 passed, mypy clean (40 files), 0 violations; both full runs started with expired running leftovers (1 then 11), and the pre-fix repro of the same state was red with `attempt=2`; a temporarily broken reaper still went red at the first-expiry assertion | 2026-09-13 23:49 |
