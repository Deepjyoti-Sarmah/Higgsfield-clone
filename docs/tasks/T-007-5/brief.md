# Brief T-007-5: Assembly + the no-JS public check

You are the **reviewer/implementer** for this final task of spec 007. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/007-share/spec.md` (AC-1, AC-3, AC-7)
- Design: `docs/specs/007-share/design.md` §§ **Flow**, **The `/v/{job_id}` HTML route and the OG/meta approach**, **Files**
- Existing: `apps/web/src/App.tsx` (the `v/:jobId` route currently renders a placeholder `EmptyState`), `apps/web/src/features/share/SharePage.tsx` (T-007-4)
- Reports to cross-check: `docs/tasks/T-007-{1..4}/report.md`

## Goal
`/v/:jobId` renders the real share page in the browser, and the **server-rendered meta tags** are proven with no JavaScript at all.

## Allowed files (touch nothing else)
- `apps/web/src/App.tsx` (edit: the `v/:jobId` route only)
- `docs/tasks/T-007-5/report.md`

## Acceptance checks
- [ ] `App.tsx`'s `v/:jobId` route renders `SharePage`; every other route, the `AppShell` wiring and the `Placeholder` usage stay exactly as they are
- [ ] `tsc -b` inside `npm run build` passes with the new route (`npm run typecheck` is a known no-op in this repo)
- [ ] **Public no-JS check (do it, and paste the evidence):** with the API up and the web app built
  (`docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run uvicorn app.main:app --port 8000`),
  create a guest + a job with `curl`, then fetch the share URL **with no cookie** and show that the raw HTML contains the meta tags:
  `curl -s http://localhost:8000/v/<job_id> | grep -Eo '<title>[^<]*</title>|property="og:[a-z:]+"|name="twitter:card"'`
  At minimum the output must include a `<title>`, `og:title`, `og:description`, `og:url` and `twitter:card`, and it must **not** require JS or a cookie. Also confirm `curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/v/<unknown-uuid>` is `200` with generic meta.
- [ ] a real browser check is optional (say SKIPPED and why if you cannot); the `curl` evidence above is the required substitute
- [ ] cross-check the T-007-1…T-007-4 reports against the code and report any mismatch (truth hierarchy: running code wins)
- [ ] `scripts/check-standards` passes; no file over 200 lines, no function over 40 lines

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any change to `features/share/**`, `api/**`, `ui/**`, the API, the contract, or the meta-tag code. If something is broken there, **report it** — do not fix it in this task.

## Report
Write `docs/tasks/T-007-5/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
