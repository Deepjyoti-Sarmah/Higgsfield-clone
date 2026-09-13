# Tasks 009: Create image (text → image)

Rules:
- One task = one agent run.
- No two **parallel** tasks share a file (checked here: 24 distinct files across the seven build tasks).
- One intentional sequential hand-off, from the designer task and committed before the successor starts (the pattern specs 003/005/007/008 used):
  - `apps/api/app/routers/image_jobs.py` — T-009-0 writes the three 501 stubs, T-009-4 replaces the bodies.
- Every task has a verify command. The full commands are in each brief.

**Waves:** T-009-0 → (T-009-1 ∥ T-009-2 ∥ T-009-3) → (T-009-4 ∥ T-009-5 ∥ T-009-6) → T-009-7.
Wave 1 puts one API-data task, one web task and one API-adapter task side by side (three different trees). Wave 2 pairs the two API halves (job surface ∥ worker) with the web UI, which only needs T-009-2. No wave has two tasks writing the same file, and no two web tasks run concurrently, so `apps/web/dist` is never raced.

- [ ] **T-009-0** · Design spec 009 + publish the contract (`image_rules`, the image schemas, the three 501 stubs, `main.py`, `openapi.json`, this file, the seven briefs)
  - Files: `docs/specs/009-image-create/**`, `docs/tasks/T-009-*/**`, `apps/api/app/domain/image_rules.py`, `apps/api/app/schemas/image_jobs.py`, `apps/api/app/routers/image_jobs.py`, `apps/api/app/main.py`, `packages/contracts/openapi.json`, `docs/{PLAN,STATUS,WORKLOG,DECISIONS}.md`, `.agent-logs/**`
  - Verify: `python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))" && ls docs/tasks | grep T-009 && scripts/check-standards`
  - Suggested role: orchestrator/designer · Depends on: —
- [ ] **T-009-1** · API data: migration `0004`, the `job.kind`/params/`output_image`/`job_image` model changes, the image repositories, and the video-only filters on the existing Library/read queries
  - Files: `apps/api/migrations/versions/0004_image_jobs.py`, `apps/api/app/models/{job,asset,job_image}.py`, `apps/api/app/repositories/{jobs,image_jobs}.py`, `apps/api/app/services/job_views.py`, `apps/api/tests/test_image_job_data.py`, `docs/tasks/T-009-1/report.md`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-009-0
- [ ] **T-009-2** · Web shared data: move the SSE watcher to `api/` (generic over the job type), add the shared balance hook, `api/imageOptions.ts` and `api/imageJobs.ts`, regenerate the client
  - Files: `apps/web/src/api/{jobStatus,jobStatusWatcher,jobStatusWatcher.test,credits,imageOptions,imageJobs}.ts`, `apps/web/src/features/create-video/{jobStatusWatcher.ts (delete),jobStatusWatcher.test.ts (delete),useJobEvents,canvasPhase,useActiveJob}.ts`, `apps/web/src/api/generated/schema.d.ts`, `docs/tasks/T-009-2/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-009-0
- [ ] **T-009-3** · API image backend: the `ImageModelAdapter` port, the pure-Python PNG placeholder, the placeholder/unconfigured adapters and `select_image_adapter`
  - Files: `apps/api/app/adapters/{image_model_adapter,png_placeholder,placeholder_image_adapter,backend_selection}.py`, `apps/api/tests/test_image_backend.py`, `docs/tasks/T-009-3/report.md`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q tests/test_image_backend.py tests/test_backend_selection.py && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-009-0
- [ ] **T-009-4** · API image surface: the create service (one transaction + HOLD), the owner read with `image_urls`/`backend`, the public options payload, and the three router bodies
  - Files: `apps/api/app/services/{image_job_creation,image_job_views,image_options}.py`, `apps/api/app/routers/image_jobs.py`, `apps/api/tests/{test_image_jobs_api,test_image_options_api}.py`, `docs/tasks/T-009-4/report.md`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-009-1, T-009-3
- [ ] **T-009-5** · API worker image step: dispatch on `ClaimedStep.kind` in the worker, the image generation run and the image success completion (SETTLE + `output_image` + `job_image`)
  - Files: `apps/api/app/services/{image_generation_runs,image_step_completion}.py`, `apps/api/app/worker.py`, `apps/api/tests/test_image_step.py`, `docs/tasks/T-009-5/report.md`
  - Verify: `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-009-1, T-009-3
- [ ] **T-009-6** · Web UI: `imageCreateCopy`, the settings/cost helpers, the page, composer, settings row, stage, result grid and failure view
  - Files: `apps/web/src/features/image-create/**`, `docs/tasks/T-009-6/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-009-2
- [ ] **T-009-7** · Assembly + slice check: route `/create/image` to `CreateImagePage` and prove the flow end to end (guest → create → SSE → images → credits)
  - Files: `apps/web/src/App.tsx`, `docs/tasks/T-009-7/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: reviewer (a different model from the T-009-6 implementer, if one is available) · Depends on: T-009-4, T-009-5, T-009-6
