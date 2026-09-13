# Brief T-008-1: API — implement `POST /api/v1/credits/topup` (the fake top-up)

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/008-credits/spec.md` (AC-4, AC-8, AC-10, AC-12)
- Design: `docs/specs/008-credits/design.md` §§ **API contract** (normative, incl. "Why `TOPUP`, not `GRANT`"), **Data**, **Flow**
- Contract: `packages/contracts/openapi.json`, path `POST /api/v1/credits/topup` → `TopUpResponse {amount, balance}` (frozen by T-008-0; the 501 stub is in `apps/api/app/routers/credits.py`)
- Existing: `apps/api/app/repositories/ledger.py` (`insert_ledger_entry`, `sum_user_balance`), `apps/api/app/repositories/users.py` (`lock_user_row`), `apps/api/app/services/credits.py` (`read_balance`), `apps/api/app/domain/credit_rules.py`, `apps/api/app/models/ledger_entry.py` (the `TOPUP` check constraints)
- Tests: `apps/api/tests/conftest.py` (`guest_client`, `client`, `session_maker`), `apps/api/tests/job_api_helpers.py` (`GUEST_GRANT`, `PRESET_COST`), `apps/api/tests/test_credits_api.py` (the existing 3-test pattern), `app.domain.credit_rules.GUEST_GRANT_CREDITS`

## Goal
Pressing "Add 100 credits" writes one **`TOPUP`** ledger row of `+100` for the caller, in one transaction, and returns the caller's new balance — with no payment and no way for a caller to pick an amount.

## Allowed files (touch nothing else)
- `apps/api/app/routers/credits.py` (replace the T-008-0 stub body)
- `apps/api/app/services/credits.py`
- `apps/api/app/domain/credit_rules.py`
- `apps/api/tests/test_credits_topup_api.py` (new)
- `docs/tasks/T-008-1/report.md`

## Must reuse
- `insert_ledger_entry` + `sum_user_balance` from `repositories/ledger.py` — no new SQL, no new repository.
- `lock_user_row` from `repositories/users.py` (the same serialisation `job_creation` uses).
- `read_balance` from `services/credits.py` as the one balance reader (do not re-sum by hand).
- `require_current_user`, `get_session`, `TopUpResponse`, `ErrorResponse` — already imported by the stub.

## Must do
- `domain/credit_rules.py`: add `TOPUP_CREDITS = 100` next to `GUEST_GRANT_CREDITS`. Do not touch `LedgerKind` or the existing constants.
- `services/credits.py`: add a frozen `TopUpResult` dataclass (`amount: int`, `balance: int`) and `async def grant_top_up_credits(session, user_id) -> TopUpResult`:
  1. `lock_user_row(session, user_id)`;
  2. `insert_ledger_entry(session, user_id=user_id, kind="TOPUP", amount=TOPUP_CREDITS)` (no `job_id` — the check constraint requires it to be NULL for `TOPUP`);
  3. `await read_balance(session, user_id)`;
  4. `await session.commit()`;
  5. return `TopUpResult(amount=TOPUP_CREDITS, balance=...)`.
  Keep it typed for `mypy --strict` (this file is under `app/services`).
- `routers/credits.py`: keep the handler **name** (`top_up_credits`), signature, `response_model=TopUpResponse` and `responses={401: {"model": ErrorResponse}}` exactly as the stub froze them — `openapi.json` must stay byte-identical. Replace only the `raise` with the service call and `TopUpResponse(amount=result.amount, balance=result.balance)`. The service name differs on purpose, so import it unambiguously.
- Tests (`test_credits_topup_api.py`, ≤200 lines):
  - `POST` with **no cookie** → **401** (`client` fixture, no cookie).
  - a fresh guest: `GET /credits` = `GUEST_GRANT_CREDITS` (60) → `POST topup` → 200 body `{"amount": 100, "balance": 160}` → `GET /credits` = 160 (AC-4, AC-8).
  - pressing twice → `{"amount": 100, "balance": 260}` and exactly **two** `TOPUP` rows (use `session_maker` + `text(...)`).
  - the row shape: `kind='TOPUP'`, `amount=100`, `job_id IS NULL`; and the guest `GRANT` row count stays **1** (proves the top-up did not touch `uq_ledger_entry_guest_grant`).
- Do **not** change `GET /api/v1/credits`, `CreditsResponse`, any model, or add a migration. There is no request body and no path/query parameter: the only declared parameter is the optional `session` cookie that `require_current_user` adds, so the frozen contract is `200`/`401`/`422` — the same response set `GET /credits` already has.

## Acceptance checks
- [ ] `POST /api/v1/credits/topup` with no cookie → 401 `ErrorResponse`
- [ ] authenticated → 200 `{amount: 100, balance: <old + 100>}`; `GET /credits` agrees immediately after
- [ ] one `TOPUP` row of `+100` with `job_id IS NULL` per call; the one-time `GRANT` is untouched
- [ ] `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` → byte-identical (the stub already froze it)
- [ ] ruff, mypy (strict on `app/services`) and the full suite are green

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards
```
Note: stop any running `app.worker` before pytest (it races the shared dev DB — see `docs/STATUS.md` BROKEN). `tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` is a known pre-existing flake; if it fails, re-run it alone and say so in the report.

## Out of scope
- Credit history (`GET /credits/entries`), a top-up cap, choosing an amount, payments.
- Any web file — T-008-2/T-008-3/T-008-4 own those.
- `apps/api/app/models/**`, migrations, `GET /credits`, `CreditsResponse`.

## Report
Write `docs/tasks/T-008-1/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
