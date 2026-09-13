# Brief T-024: real billing behind a flag (port pixovid's credits/checkout design)

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Reference: `pixovid/apps/backend/src/lib/credits.ts` (atomic spend, net-aware idempotent
  refund, packs) and `pixovid/apps/backend/src/routes/credits.ts` (order → verify → webhook)
- This repo's current billing: `apps/api/app/services/credits.py`, `apps/api/app/domain/credit_rules.py`,
  `apps/api/app/routers/credits.py` (the fake top-up)
- Decision D-013: a one-time `GRANT` is impossible via the partial unique index; the fake top-up
  writes a `TOPUP` row. Read it before touching the ledger.
- Scope note: `docs/PLAN.md` § Scope lists real payments as **CUT** for the assignment; this task
  adds the production-shaped design but must stay behind a disabled-by-default flag.

## Goal
Design and implement a **sandbox-only** billing flow: credit packs, a checkout-order endpoint,
a server-side signature verification endpoint, and a webhook backstop — disabled by default so
the assignment's fake top-up remains the demo path. Read paths trace to the same
`ledger_entry` ledger the rest of the app uses; no parallel balance.

## Decisions to copy from pixovid
- **Atomic conditional decrement** for spend (never negative); the existing ledger already does a
  lock → insert → sum, so extend rather than replace.
- **Net-aware idempotent refund**: sum SPEND minus prior REFUNDs for the reference, refund only
  the outstanding amount. A double callback must not double-refund.
- **Signature checks from exact bytes**: mount the webhook with a raw-body parser **before** the
  JSON body parser, or the signature will not match.
- **Packs are data, prices are env**: pack definitions in one module, per-action prices in settings.
- **Order receipt length limits** are a real provider footgun (pixovid hit a 40-char limit).

## Higgsfield-specific guards (do not violate)
- `BILLING_ENABLED=false` by default; with it off, `POST /credits/topup` behaves exactly as today
  and checkout returns 503/not-configured. Tests must run with it off.
- No real keys in the repo; names in `.env.example` only (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`,
  `RAZORPAY_WEBHOOK_SECRET`). Sandbox keys only, and never print them.
- This task is contract-first: publish the new paths as 501 stubs, then implement.
- If a human has not supplied sandbox keys, deliver the full design + stubs + unit tests and mark
  the live half UNVERIFIED. Do not invent an integration test that calls a real provider.

## Allowed files (touch nothing else)
- `apps/api/app/domain/credit_rules.py`, `apps/api/app/services/credits.py`, new
  `apps/api/app/services/billing.py` and `apps/api/app/adapters/payment_gateway.py`
- `apps/api/app/routers/credits.py`, new `apps/api/app/routers/billing_webhook.py`
- `apps/api/app/schemas/credits.py`, `apps/api/app/main.py` (raw-body mount only)
- `apps/api/migrations/versions/0005_*.py` (only if a migration is genuinely required)
- `packages/contracts/openapi.json`, `apps/api/tests/` (new), `.env.example`, `apps/api/app/settings.py`
- `apps/web/src/features/credits/`, `apps/web/src/api/` (packs UI behind the flag)
- `docs/specs/` (one new spec folder), `docs/tasks/T-024/{brief,report}.md`
- `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md`, `.agent-logs/*T-024*`

## Acceptance checks
- [ ] With `BILLING_ENABLED=false`: current top-up tests still pass unchanged; checkout is 503.
- [ ] With it true but no keys: startup fails loudly or checkout 503s — never a silent no-op.
- [ ] Signature verification rejects a tampered payload and accepts a valid one (unit-tested with
      a locally computed HMAC — no network).
- [ ] A duplicated webhook grants credits exactly once (idempotency test).
- [ ] Ledger invariants hold: no negative balance, every mutation has a ledger row.
- [ ] Contract diff additive only; `scripts/check-standards` passes.

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy
uv --directory apps/api run pytest -q tests/test_credits_api.py tests/test_credits_topup_api.py tests/ -k billing
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
scripts/check-standards
```

## Out of scope
- Enabling billing in production, real money, subscriptions, refunds to customers.
- Changing the guest grant (60 credits) or the 20-credit video price.

## Report
Write `docs/tasks/T-024/report.md` using `docs/templates/report.md`. ONE plain commit.
Do not mark your own work reviewed.
