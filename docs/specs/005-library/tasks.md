# Tasks 005: Library (my generations)

Rules:
- One task = one agent run.
- No two **parallel** tasks share a file (checked in T-005-0; 20 distinct files across 5 tasks).
- One intentional sequential hand-off: `apps/api/app/routers/jobs.py` — T-005-0 writes the 501 stub, T-005-1 replaces the body. T-005-0 is committed before T-005-1 starts, exactly as spec 003's T-003-0 → T-003-4 shared `app/main.py`.
- Every task has a verify command. The full commands are in each brief.

**Waves:** (T-005-1 ∥ T-005-2 ∥ T-005-3) → T-005-4 → T-005-5.
T-005-1 is API-only, T-005-2/T-005-3 are web-only and disjoint from each other, so the first three can run at once. T-005-4 consumes T-005-2 and T-005-3; T-005-5 routes and verifies the assembled page.

- [x] **T-005-0** · Design spec 005 + publish the contract (`GET /api/v1/jobs` schema + 501 stub + `openapi.json`, this file, the five briefs)
  - Files: `docs/specs/005-library/**`, `docs/tasks/T-005-*/**`, `apps/api/app/schemas/jobs.py`, `apps/api/app/routers/jobs.py`, `packages/contracts/openapi.json`
  - Verify: `python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))" && ls docs/tasks | grep T-005 && scripts/check-standards`
  - Suggested role: orchestrator/designer · Depends on: —
- [x] **T-005-1** · API: `GET /api/v1/jobs` — repository query, view builder, router body, tests
  - Files: `apps/api/app/repositories/jobs.py`, `apps/api/app/services/job_views.py`, `apps/api/app/routers/jobs.py`, `apps/api/tests/test_library_api.py`, `docs/tasks/T-005-1/report.md`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer (orchestrator for the ordering/ownership rules) · Depends on: T-005-0
- [x] **T-005-2** · Web data: move the guest-session runner to `api/guestSession.ts`, add `api/library.ts` (`useLibrary`)
  - Files: `apps/web/src/api/guestSession.ts`, `apps/web/src/features/create-video/useGuestSessionRunner.ts` (delete), `apps/web/src/features/create-video/CreateVideoPage.tsx`, `apps/web/src/api/library.ts`, `docs/tasks/T-005-2/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-005-0
- [x] **T-005-3** · Web copy + helper: `libraryCopy.ts`, `formatCreatedAt.ts` (+ test)
  - Files: `apps/web/src/features/library/libraryCopy.ts`, `apps/web/src/features/library/formatCreatedAt.ts`, `apps/web/src/features/library/formatCreatedAt.test.ts`, `docs/tasks/T-005-3/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer (small model is fine) · Depends on: T-005-0
- [ ] **T-005-4** · Web UI: `LibraryPage`, `LibraryList`, `LibraryItem`, `LibraryStates`, `LibraryResultView`, `?job=` selection
  - Files: `apps/web/src/features/library/{LibraryPage,LibraryList,LibraryItem,LibraryStates,LibraryResultView}.tsx`, `apps/web/src/features/library/useLibraryJobParam.ts`, `docs/tasks/T-005-4/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-005-2, T-005-3
- [ ] **T-005-5** · Assembly + manual check: route `/library` to `LibraryPage` and verify the signed-out flow
  - Files: `apps/web/src/App.tsx`, `docs/tasks/T-005-5/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: reviewer (a different model from the T-005-4 implementer, if one is available) · Depends on: T-005-1, T-005-4
