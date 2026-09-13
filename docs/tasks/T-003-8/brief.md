# Brief T-003-8: isolate the lease-reaper test so it stops going red in the full suite

You are the **implementer** for this one test-isolation fix. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- The failing test: `apps/api/tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` (STATUS § BROKEN has the long-standing entry).
- Its helpers: `drain_queued_steps`, `claim_step`, `expire_lease`, `reap_expired_steps` (top of the same file).
- Production code it exercises: `apps/api/app/repositories/job_steps.py` (`claim_next_queued_step` → `CLAIM_STEP_SQL`, FIFO), `apps/api/app/services/lease_reaper.py`.

## The flake (reproduce it first)
```
uv --directory apps/api run pytest -q                         # red in the full suite, ~most runs
uv --directory apps/api run pytest -q tests/test_lease_reaper.py   # green, 3/3
uv --directory apps/api run pytest -q "<the single test>"      # green, ~0.8 s
```
Failure shape: the test's **second** `claim_step` returns a step belonging to a *different* job with `attempt=2`.

Why: the suite shares one dev DB. Earlier tests leave steps whose leases have expired. The test's `reap_expired_steps(...)` is global, so it **re-queues those leftover steps too**; the next `claim_step` is FIFO (`CLAIM_STEP_SQL` orders oldest-first) and therefore picks a leftover instead of this test's own step. The guards at the top of the test (`drain_queued_steps`) only drain steps that are *queued* — a leftover already in `running` with an expired lease is not drained and comes straight back.

## Goal
The test proves the reaper's behaviour **on its own step**, deterministically, no matter what earlier tests left in the shared DB — without weakening what it asserts.

## Allowed files (touch nothing else)
- `apps/api/tests/test_lease_reaper.py`
- `apps/api/tests/conftest.py` — only if you add a reusable cleanup fixture (do not change existing fixtures' behaviour)
- `docs/tasks/T-003-8/report.md`

## Preferred fix (pick the smallest that is deterministic)
Scope the test to its own data instead of the whole table. In order of preference:
1. **Clear leftover step rows for this test.** Before creating its job, delete the rows that can be re-queued (`DELETE FROM job_step`, or scope to `status <> 'succeeded'`), so the only steps the global reaper can touch are this test's. **Do not** delete `ledger_entry`/`job`/`asset` rows for the guest: the test asserts on the guest's balance (`GUEST_GRANT - PRESET_COST`), which lives in the ledger.
2. **Claim by job.** Add a test-local helper that claims until it receives the step from *its* `job_id` (bounded, and assert it is found), instead of asserting on the first claim.

Whichever you choose: keep the test's assertions identical in strength (re-queue once, then fail + refund on the second expiry; `RELEASE` absent on the first pass).

## Acceptance checks
- [ ] `uv --directory apps/api run pytest -q` is **green** including the full suite, run at least **twice in a row** (paste both runs).
- [ ] `uv --directory apps/api run pytest -q tests/test_lease_reaper.py` is green on its own.
- [ ] Run the suite **after** at least one job-creating test file, to prove the ordering no longer matters, e.g.:
      `uv --directory apps/api run pytest -q tests/test_job_creation_api.py tests/test_library_api.py tests/test_lease_reaper.py`
- [ ] The test still fails if the reaper is broken (state in the report how you know — e.g. reason about which assertion would fire, or temporarily break `lease_reaper` locally and show it going red, then revert).
- [ ] No production behaviour change: `apps/api/app/**` untouched.
- [ ] STATUS § BROKEN's flaky-reaper row is removed in this task's docs sync (the orchestrator does the edit; tell the orchestrator in the report).
- [ ] `scripts/check-standards` passes; no file over 200 lines.

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
uv --directory apps/api run pytest -q
scripts/check-standards
```
Stop any running `app.worker` first — it races the suite on the shared dev DB.

## Out of scope
- The reaper's production logic, the claim SQL, any other test file's behaviour.
- Adding a per-test database or a transactional-rollback harness (a bigger change; if you believe it is the only correct fix, say so in the report instead of doing it).

## Report
Write `docs/tasks/T-003-8/report.md` using `docs/templates/report.md`, with both green full-suite runs pasted. Don't commit; the orchestrator handles docs sync and the commit.
