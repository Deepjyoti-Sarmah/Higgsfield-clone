# Tasks 007: Share page (`/v/{id}`)

Rules:
- One task = one agent run.
- No two **parallel** tasks share a file (checked in T-007-0; 13 distinct files across the five build tasks).
- Two intentional sequential hand-offs, both from the designer task and both committed before the successor starts (the same pattern spec 003/005 used):
  - `apps/api/app/routers/share.py` — T-007-0 writes the 501 stub, T-007-1 replaces the body.
  - `apps/api/app/main.py` — T-007-0 includes the public share router, T-007-2 includes the share-page router **before** the SPA catch-all.
- Every task has a verify command. The full commands are in each brief.

**Waves:** (T-007-1 ∥ T-007-3) → (T-007-2 ∥ T-007-4) → T-007-5.
T-007-2 needs T-007-1's public view builder; T-007-4 needs T-007-3's hook and copy. Each wave pairs one API task with one web task, so no two concurrent tasks touch the same tree.

- [x] **T-007-0** · Design spec 007 + publish the contract (`PublicJobResponse` + the 501 public route + `openapi.json`, this file, the five briefs)
  - Files: `docs/specs/007-share/**`, `docs/tasks/T-007-*/**`, `apps/api/app/schemas/share.py`, `apps/api/app/routers/share.py`, `apps/api/app/main.py`, `packages/contracts/openapi.json`
  - Verify: `python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))" && ls docs/tasks | grep T-007 && scripts/check-standards`
  - Suggested role: orchestrator/designer · Depends on: —
- [x] **T-007-1** · API: public read `GET /api/v1/public/jobs/{job_id}` — view builder, router body, tests
  - Files: `apps/api/app/routers/share.py`, `apps/api/app/services/share_views.py`, `apps/api/tests/test_share_api.py`, `docs/tasks/T-007-1/report.md`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-007-0
- [x] **T-007-2** · API: serve `/v/{job_id}` HTML with OG meta tags (no JS required)
  - Files: `apps/api/app/routers/share_page.py`, `apps/api/app/services/share_html.py`, `apps/api/app/main.py`, `apps/api/tests/test_share_page.py`, `docs/tasks/T-007-2/report.md`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer (orchestrator for the route-order/escaping details) · Depends on: T-007-1
- [x] **T-007-3** · Web data + copy: `api/share.ts` (`usePublicJob`) and `features/share/shareCopy.ts`
  - Files: `apps/web/src/api/share.ts`, `apps/web/src/features/share/shareCopy.ts`, `docs/tasks/T-007-3/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer (small model is fine) · Depends on: T-007-0
- [x] **T-007-4** · Web UI: `SharePage`, `ShareResult`, `ShareStates`
  - Files: `apps/web/src/features/share/{SharePage,ShareResult,ShareStates}.tsx`, `docs/tasks/T-007-4/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-007-3
- [ ] **T-007-5** · Assembly + public check: route `/v/:jobId` to `SharePage` and prove the no-JS meta tags
  - Files: `apps/web/src/App.tsx`, `docs/tasks/T-007-5/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: reviewer (a different model from the T-007-4 implementer, if one is available) · Depends on: T-007-1, T-007-2, T-007-4
