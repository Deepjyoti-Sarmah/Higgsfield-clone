# Report T-003-2

**Agent / model / tool:** implementer · deepseek-flash (DeepSeek Harness) · DSH agent session (no `scripts/agent-run` wrapper; transcript captured by the harness)
**Result:** DONE

## Files changed
- `apps/api/app/repositories/presets.py` (new): `list_active_presets`, `find_active_preset`.
- `apps/api/app/repositories/assets.py` (new): `insert_asset`, `find_user_asset`, `mark_asset_ready`, `find_assets_by_ids`.
- `apps/api/app/repositories/ledger.py` (new): `insert_ledger_entry`, `sum_user_balance` (`coalesce(sum, 0)`).
- `apps/api/app/repositories/jobs.py` (new): `find_job_by_idempotency_key`, `insert_job`, `find_user_job`, `find_job`, `read_job_status`, `transition_job_status` (guarded `UPDATE … WHERE status IN allowed_from`), `notify_job_event` (`SELECT pg_notify('job_events', :payload)` with `json.dumps`).
- `apps/api/app/repositories/job_steps.py` (new): frozen `ClaimedStep`/`ExpiredStep`, `insert_job_step`, `claim_next_queued_step` (`FOR UPDATE SKIP LOCKED`), `renew_step_lease`, `finish_step`, `lock_expired_steps` (`FOR UPDATE OF s SKIP LOCKED`), `requeue_step`, `fail_step`.
- `apps/api/app/repositories/users.py` (edit): added `lock_user_row` only.
- `apps/api/tests/test_job_step_repository.py` (new): double-claim, lease renewal, guarded finish, expired-lease locking.
- `apps/api/tests/test_ledger_repository.py` (new): balance sum, one-time grant, one hold per job, one resolution per job, HOLD sign check.
- `docs/tasks/T-003-2/report.md` (this file).

No other file was touched. Nothing outside the brief's allowed list was needed to make the code work.

## Reused
- `app/models/{preset,asset,job,job_step,ledger_entry,user}.py` (T-003-1) for every insert/read.
- `app/domain/credit_rules.py` literals (`LedgerKind`) and helpers (`hold_amount`, `release_amount`) in code and tests; `GUEST_GRANT_CREDITS`, `VIDEO_CREDIT_COST` in tests.
- `app/db.py` `AsyncSession` session style and the conftest `session_maker` fixture (T-003-1).
- `repositories/users.py` layer/pattern for the new repository modules.
- The `bindparam`/`text` conventions from `tests/test_migrations.py`; `pytest.raises(IntegrityError)` on `flush()` for the constraint tests.

## Verify output (full paste, no summarising)
Commands were run as one chained block (`docker compose up -d --wait db` → `alembic upgrade head` → `ruff check .` → `mypy` → `pytest -q` → `scripts/check-standards`):

```
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
All checks passed!
Success: no issues found in 12 source files
.............................                                            [100%]
29 passed in 6.22s
check-standards: ok (0 violations)
```

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **`test_migrations.py` breaks as soon as any `job` row exists (needs the orchestrator).** T-003-1's test runs `alembic downgrade 0001`, whose `0003` downgrade deletes the 12 presets; any surviving `job.preset_slug` reference then raises `ForeignKeyViolationError: job_preset_slug_fkey`. My first two runs left such rows behind and the full suite failed on it. I cannot edit `test_migrations.py` or `conftest.py` (both owned elsewhere), so I fixed it from inside my two allowed test files: an autouse teardown deletes exactly the rows each test created (`job_step` → `ledger_entry` → `job` → `asset` → `app_user`, scoped to the user ids that test created), and I manually removed the rows my pre-fix runs had left in the dev DB. **T-003-4's API tests create jobs and will re-break this test unless `test_migrations.py`/`conftest.py` grows a cleanup or the migration test stops assuming an unreferenced preset table.** This is the one real problem I could not fix within my allowed files.
- **Model registration (a gotcha for T-003-3/4/5).** Because `job.preset_slug` FKs `preset.slug`, SQLAlchemy `configure_mappers()` fails with `NoReferencedTableError` unless *every* model module is imported in the process. `app/models/__init__.py` is empty and not mine to edit, so each repository module carries `from app.models import …  # noqa: F401 (FK registration)` plus the specific model it uses. T-003-3/4/5 should import repository modules rather than raw model classes so they inherit this.
- **Guesses (small, documented):** `mark_asset_ready` sets `updated_at = datetime.now(UTC)` (the models have no `onupdate`); `finish_step` also writes `updated_at = now()` (the design SQL omitted it, but claim/renew/reaper all keep it fresh); `transition_job_status` writes `error_message`/output ids/`started_at`/`finished_at` only when a value is passed, so a reaper re-queue does not clear them. `transition_job_status` types `allowed_from` as `Collection[str]` so callers can pass either `{"queued"}` or `statuses_allowed_before(...)` without a mypy fight.
- **Duplicated test helper.** The row-cleanup helper and fixture exist in both test files; the rule-of-two extraction would go to `tests/conftest.py`, which is out of scope (T-003-1 owns it). Same reason the fixtures are per-file.
- No schema change was needed: every column/index the brief mentions already exists from T-003-1.
- No paid generation was run; `GENERATION_BACKEND=mock` (set by conftest) was in effect throughout.
- Not committed (the orchestrator commits). `.agent-logs/` untouched by me.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Repositories (presets, assets, ledger, jobs, job steps) with claim/lease/reaper SQL + NOTIFY | `apps/api/app/repositories/{presets,assets,ledger,jobs,job_steps}.py`, `users.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/check-standards` (29 passed) | 2026-09-13 02:45 |
