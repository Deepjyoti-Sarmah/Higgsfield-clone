# Report T-008-1

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE

## Files changed
- `apps/api/app/domain/credit_rules.py` (edit): added `TOPUP_CREDITS = 100` next to `GUEST_GRANT_CREDITS`. `VIDEO_CREDIT_COST`, `MAX_STEP_ATTEMPTS`, `LedgerKind`, `hold_amount`, `release_amount` are untouched.
- `apps/api/app/services/credits.py` (edit, 9 → 26 lines): added the frozen `TopUpResult` dataclass (`amount: int`, `balance: int`) and `async def grant_top_up_credits(session, user_id) -> TopUpResult` — `lock_user_row` → `insert_ledger_entry(kind="TOPUP", amount=TOPUP_CREDITS)` (no `job_id`) → `read_balance` → `commit` → `TopUpResult`. `read_balance` is unchanged and is still the only balance reader.
- `apps/api/app/routers/credits.py` (edit, 35 → 34 lines): replaced the T-008-0 stub's `raise HTTPException(501)` with `grant_top_up_credits(...)` → `TopUpResponse(amount=..., balance=...)`. The handler **name** (`top_up_credits`), signature, `response_model=TopUpResponse` and `responses={401: {"model": ErrorResponse}}` are untouched, so `openapi.json` is byte-identical. The now-unused `HTTPException`/`status` imports were dropped (ruff `F401` would otherwise fail); no request body, path or query parameter was added.
- `apps/api/tests/test_credits_topup_api.py` (new, 76 lines): 5 tests — no-cookie 401; fixed amount + the returned/`GET` balance agreeing; repeatability (60 → 160 → 260); one job-less `TOPUP` row per call; the one-time `GRANT` left untouched.
- `docs/tasks/T-008-1/report.md`: this report.

## Reused
- `repositories/ledger.py::insert_ledger_entry` + `sum_user_balance` — no new SQL, no new repository.
- `repositories/users.py::lock_user_row` — the same per-user serialisation `job_creation` uses.
- `services/credits.py::read_balance` as the single balance reader (no hand-rolled sum).
- `require_current_user`, `get_session`, `TopUpResponse`, `ErrorResponse` (already wired by the frozen stub), the pre-provisioned `TOPUP` kind and its check constraints / partial indexes.
- Test fixtures `client`, `guest_client`, `session_maker` and the helper `current_user_id` — the same pattern as `test_credits_api.py`.

## Verify output (full paste, no summarising)
Command run exactly as given in the brief, from the repo root, with per-step exit codes (the chain is `&&`-joined):
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
docker exit=0
alembic exit=0
All checks passed!
ruff exit=0
Success: no issues found in 31 source files
mypy exit=0
........................................................................ [ 54%]
.............................................................            [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
133 passed, 2 warnings in 64.45s (0:01:04)
pytest exit=0
wrote packages/contracts/openapi.json
export exit=0
contract-diff exit=0
check-standards: ok (0 violations)
standards exit=0
```
`alembic upgrade head` and `docker compose up -d --wait db` exited 0 (no pending migration, as designed). `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` exited **0**: the frozen contract is byte-identical (it does not even appear in `git status`), so the T-008-0 stub's name/signature/response map survived the body replacement.

**Two honest notes on the runs.** A worker was checked first and none was running. The **first** full-suite run failed on the known pre-existing flake `tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` (it claimed another test's queued step), with **132 passed, 1 failed** — the flake documented in `docs/STATUS.md` BROKEN and unrelated to credits. Isolated re-run → `1 passed in 1.40s`, and the green full run pasted above followed (**133 passed** = 128 + my 5). The contract-diff and standards steps were already green on the first run.

Extra live evidence against the running `uvicorn --reload` on `:8000` (not required by the brief):
```
$ curl -s -o /dev/null -w '%{http_code}' -X POST .../api/v1/credits/topup        # no cookie
401
$ curl -s -c /tmp/c -X POST .../api/v1/auth/guest                                 # 201
balance before: {"balance":60}
topup 1:        {"amount":100,"balance":160}
topup 2:        {"amount":100,"balance":260}
balance after:  {"balance":260}

$ docker exec higgsfield-db-1 psql -U postgres -d higgsfield -tAc \
    "SELECT kind, amount, job_id FROM ledger_entry WHERE user_id = (SELECT id FROM app_user ORDER BY created_at DESC LIMIT 1) ORDER BY created_at;"
GRANT|60|
TOPUP|100|
TOPUP|100|
```
The last column is empty for both `TOPUP` rows, i.e. `job_id IS NULL` — the check constraint's requirement and the "free credits that belong to no job" semantics.

## Standards check
```
check-standards: ok (0 violations)
```
File sizes: `routers/credits.py` 34 · `services/credits.py` 26 · `domain/credit_rules.py` 16 · `tests/test_credits_topup_api.py` 76 — all far under 200. Functions are 3–21 lines (limit 40); ruff `C90` (max complexity 8) is green. `mypy --strict` passes over `app/services` (31 files), so `TopUpResult` / `grant_top_up_credits` are fully typed.

## Acceptance checks
- [x] `POST /api/v1/credits/topup` with no cookie → **401** `ErrorResponse` (`test_topup_without_a_cookie_is_unauthorized`; live curl 401).
- [x] Authenticated → 200 `{amount: 100, balance: <old + 100>}` and `GET /credits` agrees immediately after (`test_topup_grants_the_fixed_amount_and_returns_the_new_balance`; live 60 → 160 → `GET` 160).
- [x] One `TOPUP` row of `+100` with `job_id IS NULL` per call; the one-time `GRANT` is untouched (`test_each_topup_writes_one_jobless_topup_row`, `test_topup_leaves_the_one_time_guest_grant_untouched`; live `GRANT|60|`, `TOPUP|100|`, `TOPUP|100|`). The `TOPUP` kind is used deliberately instead of `GRANT` — a second `GRANT` would violate `uq_ledger_entry_guest_grant` (design § "Why `TOPUP`, not `GRANT`", D-013).
- [x] `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` → **byte-identical** (exit 0).
- [x] ruff, mypy (strict) and the full suite green (**133 passed**).

## Open issues / guesses / things skipped
- **No migration, no model change, no `GET /credits` change** — as designed; `TOPUP` and `ix_ledger_entry_user` already existed.
- **The service is named `grant_top_up_credits`, the handler `top_up_credits`.** The handler name is frozen by the T-008-0 stub (it is what yields `openapi.json`'s operationId), so the service could not share it without an import collision in the router. Documented in the brief and design.
- **No cap and no history**, per the spec's P0 cuts; the route is intentionally repeatable (one `TOPUP` row per call) and both behaviours are asserted.
- **The first verify run was red on the known reaper flake**, not on this change; the isolated pass and the green re-run are recorded above, and nothing in this task touches job steps, leases or the reaper.
- Other sessions' files (`apps/web/src/api/credits.ts`, `apps/web/src/features/credits/**`, `apps/web/src/App.tsx`, `schema.d.ts`, `docs/tasks/T-008-{2,3}/report.md`) are present in the shared tree and are **not mine**; they do not affect this API-only verify. Nothing was committed — the orchestrator does that.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| `POST /api/v1/credits/topup` live: any guest can add a fixed **+100** fake credits (no payment, no body, amount not caller-chosen); one transaction (lock → `TOPUP` row → sum → commit) returns `{amount, balance}`; repeatable; the one-time `GRANT` is untouched; contract byte-identical | `apps/api/app/routers/credits.py`, `apps/api/app/services/credits.py`, `apps/api/app/domain/credit_rules.py`, `apps/api/tests/test_credits_topup_api.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` → 133 passed (5 new), mypy clean (31 files), contract byte-identical, 0 violations; live 60 → 160 → 260 with `GRANT|60|` + two `TOPUP|100|` rows (`job_id` NULL) | 2026-09-13 22:32 |
