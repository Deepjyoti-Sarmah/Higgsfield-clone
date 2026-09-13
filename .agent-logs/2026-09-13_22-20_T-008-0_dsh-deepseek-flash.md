---
session_id: b48f72ef
date: 2026-09-13
author: Deepjyoti-Sarmah
model: deepseek-flash
tool: dsh
project: higgsfield-rebuild
total_exchanges: 1
---

# Session Log - 2026-09-13 · T-008-0 design spec 008 Credits + fake top-up + contract (hand-exported from DSH)

DSH (deepseek-flash) transcript for the T-008-0 orchestrator/designer turn: the user prompt and the assistant's messages. Tool calls and reasoning are omitted; text is verbatim. This log is a **hand export** — the repo's `.claude/hooks/capture.py` covers Claude Code, not this harness, so the agent wrote it in the same format the committed T-005-0/T-007-0 DSH logs use.

---

[LOG_ENTRY type=PROMPT num=1 session=b48f72ef]
model: user

You are the ORCHESTRATOR / DESIGNER for spec 008 (Credits + fake top-up). Work alone; the
repo is shared, read it fresh first.

READ FIRST:
1. AGENTS.md, docs/STANDARDS.md
2. docs/playbooks/spec-new.md
3. docs/research/product-map.md — "Credits with a fake top-up covers the money flow (D-007)",
   and row "Generate button shows the credit cost up front" (already done in spec 004)
4. docs/DECISIONS.md — D-007 (fake top-up), D-001/D-002/D-006 as relevant
5. docs/specs/003-generation-core/design.md § Credits/ledger (the ledger is already HOLD/
   SETTLE/RELEASE + the one-time 60-credit guest GRANT)
6. packages/contracts/openapi.json — GET /api/v1/credits exists; there is NO top-up route.

GOAL
Design the Credits page (`/credits`, currently a placeholder) and the fake top-up: show the
balance (reuse GET /api/v1/credits), and a "fake" top-up that grants a fixed amount (e.g.
"Add 100 credits") with NO payment — a new POST endpoint that writes a GRANT ledger row and
returns the new balance. Cover: signed-out → auto-guest, the balance states (loading/error/
known), the top-up action (idle/pending/done/error), and any credit-history list if in P0
scope. Keep it P0-simple; real payments are CUT (D-007).

DELIVER (under docs/specs/008-credits/):
- spec.md (testable AC-N, all four UI states, out of scope)
- design.md (API contract first, Files table, AC→design→task map)
- tasks.md (one task = one agent run; disjoint files; waves; first task = routes + schemas
  + regenerate openapi.json)
- docs/tasks/T-008-{1..k}/brief.md
- The contract additions (schemas + 501 router stub + scripts/export-openapi) for the top-up
  route — do NOT change existing routes/schemas.

VERIFY (paste full output in docs/tasks/T-008-0/report.md):
  python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))"
  ls docs/tasks | grep T-008
  scripts/check-standards

Then tick T-008-0 in docs/PLAN.md, update docs/STATUS.md + docs/WORKLOG.md, commit plain
(no Co-Authored-By trailers), including .agent-logs/.

[LOG_ENTRY type=RESPONSE num=1 session=b48f72ef]
model: deepseek-flash

Read the required sources fresh (AGENTS.md, STANDARDS.md, spec-new.md, product-map credits rows, DECISIONS D-001/2/6/7/12, the 003 ledger design, the whole credits stack, the 005/006/007 packs and templates). Two findings shaped the design:

1. **`GRANT` cannot be the top-up kind.** `uq_ledger_entry_guest_grant` is a partial unique index on `(user_id) WHERE kind = 'GRANT'`, and every guest already received that one-time grant at account creation — a second `GRANT` is a unique violation. The ledger already pre-provisions `TOPUP` in `ck_ledger_entry_kind`, in `LedgerKind`, and in the amount-sign check (positive, `job_id IS NULL`), and it has never been written. The route uses `TOPUP`; **no migration**.
2. **Scope conflict.** D-012 lists "pricing with a fake top-up" under P1, while `docs/PLAN.md` § Scope and D-007 put it in the P0 loop. Per the direct instruction (P0-simple) and PLAN.md, spec 008 is P0; new decision **D-013** records the resolution (DECISIONS is append-only).

Delivered:
- `docs/specs/008-credits/spec.md` — AC-1…AC-12, all UI states, out-of-scope incl. the two deliberate P0 cuts (no history list, no cap).
- `docs/specs/008-credits/design.md` — contract first, "Why `TOPUP`, not `GRANT`", no-migration data section, flow (lock → insert → sum → commit), component tree + exact props, copy table, accessibility, Files table, Reused, Risks.
- `docs/specs/008-credits/tasks.md` — waves `T-008-0 → (T-008-1 ∥ T-008-2) → T-008-3 → T-008-4`, 11 distinct files, one declared sequential hand-off on `routers/credits.py`.
- `docs/tasks/T-008-{1,2,3,4}/brief.md`.
- Contract: `+ TopUpResponse {amount, balance}` in `apps/api/app/schemas/credits.py`; the `POST /credits/topup` 501 stub in `apps/api/app/routers/credits.py`; `scripts/export-openapi` → `packages/contracts/openapi.json` **+77/−0**, with a structural diff proving 0 pre-existing paths and 0 pre-existing schemas changed.

Caught and corrected one of my own errors: the design first claimed the contract has "no 422". Because `require_current_user` declares an optional `session` cookie parameter, FastAPI emits a 422 — the same response set the existing `GET /credits` already has. `design.md` and the T-008-1 brief now say `200`/`401`/`422`.

[LOG_ENTRY type=RESPONSE num=1 session=b48f72ef]
model: deepseek-flash

Verify command output (also pasted in `docs/tasks/T-008-0/report.md`):

```
$ python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))"
/api/health
/api/v1/auth/guest
/api/v1/credits
/api/v1/credits/topup
/api/v1/jobs
/api/v1/jobs/{job_id}
/api/v1/jobs/{job_id}/events
/api/v1/me
/api/v1/presets
/api/v1/public/jobs/{job_id}
/api/v1/uploads
/api/v1/uploads/{asset_id}/complete

$ ls docs/tasks | grep T-008
T-008-0
T-008-1
T-008-2
T-008-3
T-008-4

$ scripts/check-standards
check-standards: ok (0 violations)
```

Live stub probe against the running `uvicorn --reload` on `:8000`:
```
$ curl -s -i -X POST http://127.0.0.1:8000/api/v1/credits/topup        # no cookie → 401
$ curl -s -c /tmp/c -X POST http://127.0.0.1:8000/api/v1/auth/guest    # 201
$ curl -s -b /tmp/c -i -X POST http://127.0.0.1:8000/api/v1/credits/topup   # 501 stub
$ curl -s -b /tmp/c http://127.0.0.1:8000/api/v1/credits               # {"balance":60}
```

Ticking T-008-0 in `docs/PLAN.md`, updating `docs/STATUS.md` + `docs/WORKLOG.md`, and committing the T-008-0 change set (plain message, no attribution trailers).
