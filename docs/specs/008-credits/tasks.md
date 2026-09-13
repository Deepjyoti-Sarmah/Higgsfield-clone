# Tasks 008: Credits + fake top-up

Rules:
- One task = one agent run.
- No two **parallel** tasks share a file (checked here: 11 distinct files across the four build tasks).
- One intentional sequential hand-off, from the designer task and committed before the successor starts (the same pattern specs 003/005/007 used):
  - `apps/api/app/routers/credits.py` — T-008-0 writes the 501 stub, T-008-1 replaces the body.
- Every task has a verify command. The full commands are in each brief.

**Waves:** T-008-0 → (T-008-1 ∥ T-008-2) → T-008-3 → T-008-4.
T-008-1 (API) and T-008-2 (web data) touch different trees and are parallel-safe. T-008-3 needs T-008-2's hook and types; T-008-4 needs T-008-3's page. No wave has two tasks writing the same file, and no two web tasks run concurrently, so the `apps/web/dist` build is never raced.

- [ ] **T-008-0** · Design spec 008 + publish the contract (`TopUpResponse` + the 501 top-up route + `openapi.json`, this file, the four briefs)
  - Files: `docs/specs/008-credits/**`, `docs/tasks/T-008-*/**`, `apps/api/app/schemas/credits.py`, `apps/api/app/routers/credits.py`, `packages/contracts/openapi.json`, `docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md`, `docs/DECISIONS.md`, `.agent-logs/**`
  - Verify: `python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))" && ls docs/tasks | grep T-008 && scripts/check-standards`
  - Suggested role: orchestrator/designer · Depends on: —
- [ ] **T-008-1** · API: implement `POST /api/v1/credits/topup` — `TOPUP_CREDITS`, the service, the router body, tests
  - Files: `apps/api/app/routers/credits.py`, `apps/api/app/services/credits.py`, `apps/api/app/domain/credit_rules.py`, `apps/api/tests/test_credits_topup_api.py`, `docs/tasks/T-008-1/report.md`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-008-0
- [ ] **T-008-2** · Web data: `api/credits.ts` (`useCreditsPage`) + regenerate the typed client
  - Files: `apps/web/src/api/credits.ts`, `apps/web/src/api/generated/schema.d.ts`, `docs/tasks/T-008-2/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer (a small model is fine) · Depends on: T-008-0
- [ ] **T-008-3** · Web UI: `creditsCopy`, `CreditsBalanceCard`, `CreditsTopUpCard`, `CreditsPage`
  - Files: `apps/web/src/features/credits/{creditsCopy,CreditsBalanceCard,CreditsTopUpCard,CreditsPage}.ts(x)`, `docs/tasks/T-008-3/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-008-2
- [ ] **T-008-4** · Assembly + manual check: route `/credits` to `CreditsPage` and prove the signed-out top-up
  - Files: `apps/web/src/App.tsx`, `docs/tasks/T-008-4/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: reviewer (a different model from the T-008-3 implementer, if one is available) · Depends on: T-008-1, T-008-3
