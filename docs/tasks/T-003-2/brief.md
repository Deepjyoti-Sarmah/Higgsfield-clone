# Brief T-003-2: Repositories (SQL for presets, assets, ledger, jobs, job steps)

You are the **orchestrator-grade implementer** for this one task (the claim/lease SQL is the risky core). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/003-generation-core/spec.md` (AC-3, AC-4, AC-5, AC-7 data access; AC-9 double-claim)
- Design: `docs/specs/003-generation-core/design.md` sections **Data**, **Flow 1–6** (the SQL), **Repository signatures**, **Test plan** (T-003-2 rows)
- Pattern: `apps/api/app/repositories/users.py`

## Goal
Every repository function in design § Repository signatures exists with exactly that signature, so T-003-3, T-003-4 and T-003-5 can code against them in parallel.

## Allowed files (touch nothing else)
- `apps/api/app/repositories/{presets,assets,ledger,jobs,job_steps}.py`
- `apps/api/app/repositories/users.py` (add `lock_user_row` only)
- `apps/api/tests/test_job_step_repository.py`, `apps/api/tests/test_ledger_repository.py`
- `docs/tasks/T-003-2/report.md`

## Rules
- Repositories only `flush()`, never `commit()`, and contain no business rules (the caller passes `allowed_from`, amounts, statuses).
- `claim_next_queued_step`, `renew_step_lease`, `finish_step`, `lock_expired_steps` use the SQL written in the design (`FOR UPDATE SKIP LOCKED`, guarded by `lease_owner` and `status`).
- `notify_job_event` runs `SELECT pg_notify('job_events', :payload)` with `json.dumps({"job_id": str(job_id)})` as a bind parameter.
- `ClaimedStep(id, job_id, kind, attempt)` and `ExpiredStep(id, job_id, attempt, user_id, credit_cost)` are frozen dataclasses defined in `job_steps.py`.

## Must reuse
- Models, `domain/credit_rules.py` literals and the fixtures (`session_maker`, `guest_client`) from T-003-1.

## Acceptance checks
- [ ] **Double-claim:** with exactly one queued step, two sessions from `session_maker` call `claim_next_queued_step` concurrently (`asyncio.gather`, each in its own transaction) → exactly one returns a `ClaimedStep`, the other `None`
- [ ] `renew_step_lease` / `finish_step` return `False` for a different `worker_id` and `True` for the owner
- [ ] `lock_expired_steps` returns a step whose `lease_expires_at` is in the past and skips one locked by another open transaction
- [ ] Ledger: `sum_user_balance` equals the sum of inserted amounts (0 with no rows); a second GRANT, a second HOLD for one job, and SETTLE after RELEASE each raise `IntegrityError`; a positive HOLD violates the sign check
- [ ] Tests create their own users/jobs and don't depend on other rows in the shared dev DB. The double-claim test first drains leftover queued steps (claim until `None`, with a throwaway worker id), then creates exactly one step and asserts the winner got that step's id

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
scripts/check-standards
```

## Out of scope
- Services, routers, the worker loop, transactions/commits (T-003-3…5).
- Schema changes. If a column or index is missing, stop and write it in the report.

## Report
Write `docs/tasks/T-003-2/report.md` using `docs/templates/report.md`, then follow the definition of done in `AGENTS.md` (commit per the kickoff prompt, plain message, no trailers, include `.agent-logs/`).
