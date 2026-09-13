# Brief T-008-4: Assembly — route `/credits` and verify the signed-out top-up

You are the **reviewer/implementer** for this final task of spec 008. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/008-credits/spec.md` (AC-1, AC-2, AC-4, AC-12)
- Design: `docs/specs/008-credits/design.md` §§ **Flow**, **Component tree**, **Files**
- Existing: `apps/web/src/App.tsx` (the `credits` route currently renders `<Placeholder title="Credits" />`), `apps/web/src/features/credits/CreditsPage.tsx` (T-008-3)
- Reports to cross-check: `docs/tasks/T-008-{1..3}/report.md`

## Goal
`/credits` renders the real Credits page, and the fake top-up is exercised end to end over HTTP — signed out first, then as a guest whose balance actually grows in the ledger.

## Allowed files (touch nothing else)
- `apps/web/src/App.tsx` (edit: the `credits` route only)
- `docs/tasks/T-008-4/report.md`

## Acceptance checks
- [ ] `App.tsx`'s `credits` route renders `CreditsPage`; every other route, the `AppShell` wiring, the `Placeholder` usage and all other imports stay exactly as they are
- [ ] `tsc -b` inside `npm run build` passes with the new route (`npm run typecheck` is `tsc -b` since T-000-6 and is a real gate)
- [ ] **Manual signed-out check** (record it in the report; SKIPPED is only acceptable if you say why): with the API up (`docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head`; a `uvicorn app.main:app` on `:8000` serving the freshly built `apps/web/dist`) prove with `curl` that
  1. `POST /api/v1/credits/topup` with **no cookie** → **401**;
  2. creating a guest (`POST /api/v1/auth/guest`, 201) then `GET /api/v1/credits` → `{"balance": 60}`;
  3. `POST /api/v1/credits/topup` as that guest → `{"amount": 100, "balance": 160}`, and a repeat → `{"amount": 100, "balance": 260}`;
  4. `GET /api/v1/credits` still returns `{"balance": 260}` (the ledger, not memory);
  5. `GET /credits` is a routable SPA path (200 with the built `index.html`), and the served bundle contains the Credits copy. If a browser is unavailable, say so — the curl-level check plus a bundle grep is the accepted substitute;
  6. do **not** leave a dev `app.worker` running against the shared DB, and stop any server you started yourself.
- [ ] cross-check the T-008-1…T-008-3 reports against the code: report any mismatch between a report's claim and what the code does (truth hierarchy: running code wins). Include the `TOPUP`-vs-`GRANT` decision from design § API contract if a report words it differently.
- [ ] `scripts/check-standards` passes; no file over 200 lines, no function over 40 lines

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any change to `features/credits/**`, `api/**`, `ui/**`, the API, the contract, or the placeholder usage for `create/image`. If something is broken there, **report it** — do not fix it in this task.
- Credit history, a top-up cap, payments.

## Report
Write `docs/tasks/T-008-4/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
