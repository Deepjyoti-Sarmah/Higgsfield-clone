# Tasks 002: Walking skeleton

Rules: one task = one agent run; parallel tasks don't share files; every task has a verify command.

- [x] **T-002-1** · API skeleton: settings, db, health, `app_user` + migration, guest session, worker heartbeat, tests, openapi export
  - Files: `apps/api/**`, `docker-compose.yml`, `.env.example`, `scripts/export-openapi`, `packages/contracts/openapi.json`
  - Verify: `docker compose up -d db && cd apps/api && uv run ruff check . && uv run pytest -q && cd ../.. && scripts/export-openapi && scripts/check-standards`
  - Role: orchestrator (sets the patterns) · Depends on: —
- [ ] **T-002-2** · Web shell: Vite React TS, dark theme tokens, AppShell nav, guest button with all 4 states, generated client, eslint rules from STANDARDS
  - Files: `apps/web/**`
  - Verify: `cd apps/web && npm run gen:api && npm run lint && npm run typecheck && npm run build && cd ../.. && scripts/check-standards`
  - Role: implementer (any coding model) · Depends on: T-002-1 (openapi.json)
- [ ] **T-002-3** · Container: Dockerfile (web build → python), `APP_ROLE` entrypoint, `railway.json`
  - Files: `Dockerfile`, `.dockerignore`, `railway.json`, `apps/api/entrypoint.sh`
  - Verify: `docker build -t hf-clone . && docker run --rm --network host --env-file .env.local hf-clone` then `curl localhost:8000/api/health` and `curl localhost:8000/` (HTML)
  - Role: orchestrator · Depends on: T-002-1, T-002-2
- [ ] **T-002-4** · Deploy: Neon DB, Railway `api` + `worker` services, env vars, migrations on release
  - Files: `docs/STATUS.md`, `README.md`
  - Verify: `curl https://<live>/api/health` → ok; `railway logs --service worker` shows a heartbeat
  - Role: orchestrator · Depends on: T-002-3 + **user credentials**
- [ ] **T-002-5** · Modal spike: LTX-2.5 distilled image→video → R2
  - Files: `apps/gpu/**`
  - Verify: `modal run apps/gpu/ltx_spike.py --image <url> --prompt "slow dolly in"` prints the R2 key + seconds
  - Role: orchestrator · Depends on: **Modal token + R2 keys** (can run in parallel with 1–3)
- [ ] **T-002-6** · verify-slice on the live URL (AC-1..AC-5), with screenshots in `docs/verification/002-walking-skeleton/`
  - Files: `docs/verification/**`, `docs/STATUS.md`
  - Verify: the playbook checklist
  - Role: reviewer (a different model from the implementers) · Depends on: T-002-4
