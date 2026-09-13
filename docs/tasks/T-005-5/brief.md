# Brief T-005-5: Assembly — route `/library` and verify the signed-out flow

You are the **reviewer/implementer** for this final task of spec 005. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/005-library/spec.md` (AC-1, AC-2, AC-5)
- Design: `docs/specs/005-library/design.md` §§ **Flow**, **Component tree**, **Files**
- Existing: `apps/web/src/App.tsx` (the `library` route currently renders `<Placeholder title="Library" />`), `apps/web/src/features/library/LibraryPage.tsx` (T-005-4)
- Reports to cross-check: `docs/tasks/T-005-{1..4}/report.md`

## Goal
`/library` renders the real Library page, and the assembled feature is exercised end to end far enough to trust it.

## Allowed files (touch nothing else)
- `apps/web/src/App.tsx` (edit: the `library` route only)
- `docs/tasks/T-005-5/report.md`

## Acceptance checks
- [ ] `App.tsx`'s `library` route renders `LibraryPage`; the `Placeholder` import/usage for the other routes and every other route stay exactly as they are
- [ ] `tsc -b` inside `npm run build` passes with the new route (this repo's `npm run typecheck` is a known no-op)
- [ ] **Manual check** (record it in the report; SKIPPED is only acceptable if you say why): with the API up (`docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run uvicorn app.main:app --port 8000`) and the web app built, confirm with `curl` that a signed-out `GET /api/v1/jobs` returns **401**, and that `/library` is a routable SPA path (200 with the built `index.html`). If a browser is unavailable, say so — a curl-level check plus a bundle grep is the accepted substitute
- [ ] cross-check the T-005-1…T-005-4 reports against the code: report any mismatch between a report's claim and what the code does (truth hierarchy: running code wins)
- [ ] no file over 200 lines, no function over 40 lines; `scripts/check-standards` passes

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any change to `features/library/**`, `api/**`, `ui/**`, the API, or the contract. If something is broken there, **report it** — do not fix it in this task.

## Report
Write `docs/tasks/T-005-5/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
