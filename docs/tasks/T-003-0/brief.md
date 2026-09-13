# Brief T-003-0: Design spec 003 (generation core) + publish its API contract

You are the **designer** (needs the strongest reasoning model available) for this one task. First steps:
1. Read `AGENTS.md`, `docs/STATUS.md` and `docs/STANDARDS.md`.
2. Read every link below.
3. Follow `docs/playbooks/spec-new.md` steps 4–7.

## Context links
- Spec: `docs/specs/003-generation-core/spec.md` (AC-1 … AC-9). Handing it off counts as the user's approval, so set Status: APPROVED.
- Architecture invariants: `docs/architecture/architecture.md`; decisions D-001, D-002, D-003, D-006 in `docs/DECISIONS.md`
- Existing code to follow and reuse (the patterns are set; don't re-invent them):
  - `apps/api/app/db.py`: `Base`, `get_session`, `create_database_engine`
  - `apps/api/app/auth_dependencies.py`: `require_current_user`
  - `apps/api/app/settings.py`: add new settings here
  - `apps/api/app/routers/auth.py`, `services/guest_accounts.py`, `repositories/users.py`: layering example
  - `apps/api/tests/conftest.py`: `open_client` fixture pattern
  - `apps/api/migrations/versions/0001_create_app_user.py`: migration style
- Templates: `docs/templates/design.md`, `docs/templates/tasks.md`, `docs/templates/delegation-brief.md`

## Goal
Turn spec 003 into a design that other agents can build **in parallel without talking to each other**, and publish the contract early, so the UI (spec 004) can start before the backend is finished.

## Deliverables
1. **`docs/specs/003-generation-core/design.md`** covering:
   - **API contract table:** every endpoint in the spec, with request/response schema names and error codes.
   - **Data:** tables `asset`, `preset`, `job`, `job_step`, `ledger_entry`, with columns, types, FKs and indexes. Must include:
     - a unique `(user_id, idempotency_key)` on `job`
     - a partial index for claiming queued steps
     - ledger `kind` ∈ GRANT/HOLD/SETTLE/RELEASE/TOPUP
     - migration names
   - **Flow:**
     - the create-job transaction
     - the claim SQL (`FOR UPDATE SKIP LOCKED`, lease columns)
     - heartbeat/lease renewal and the reaper rule
     - the NOTIFY payload (ids only, < 8000 bytes)
     - the SSE fan-out (ONE dedicated LISTEN connection per API process → per-job `asyncio.Queue`s, 20s ping)
   - **`ModelAdapter` Protocol** signature, plus the `local-motion`, `mock`, `modal`, `openrouter` implementations, and backend selection via `GENERATION_BACKEND`.
   - **The 12 presets:** slug, name, category, `credit_cost`, and the exact ffmpeg motion recipe for each (zoompan/crop/rotate expressions, 5s, 24fps, ≤720p, h264 + faststart, poster frame).
   - **Storage:** an `ObjectStorage` Protocol (S3-compatible: MinIO locally, R2 later), presigned PUT/GET, key layout.
   - **Files table:** every file created or edited with a one-line responsibility, each ≤200 lines, following the layer rules in STANDARDS.
   - **Reused** and **Risks** sections.
2. **`docs/specs/003-generation-core/tasks.md`:** 5–8 tasks (`T-003-1…`), each one agent run with a **disjoint** file set, a verify command, dependencies and a suggested role. T-003-1 must be "contract + migrations".
3. **`docs/tasks/T-003-k/brief.md`** for every task in tasks.md, filled in from the template (not skeletons).
4. **The contract, published now:**
   - Pydantic schemas in `apps/api/app/schemas/` for every endpoint.
   - Routers in `apps/api/app/routers/` whose handlers return `501 Not Implemented`, included in `app/main.py`.
   - Regenerate `packages/contracts/openapi.json` with `scripts/export-openapi`.

## Allowed files
- `docs/specs/003-generation-core/**`, `docs/tasks/T-003-*/**`
- `apps/api/app/schemas/{presets,uploads,jobs,credits}.py`, `apps/api/app/routers/{presets,uploads,jobs,credits}.py`, `apps/api/app/main.py`
- `packages/contracts/openapi.json`
- `docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md`

## Must reuse
- The existing layering, `get_session`, `require_current_user` and the test fixture style listed above. Don't add new frameworks (no Celery, no Redis).

## Acceptance checks
- [ ] Every AC in spec 003 maps to a section of design.md and to at least one task
- [ ] No two tasks in tasks.md share a file (parallel-safe)
- [ ] Every T-003-k brief has its allowed files, verify command and out-of-scope filled in
- [ ] `openapi.json` contains all spec-003 endpoints; existing tests still pass

## Verify command (paste the full output in report.md)
```
docker compose up -d --wait db
uv --directory apps/api run ruff check .
uv --directory apps/api run pytest -q
scripts/export-openapi
python3 -c "import json;p=json.load(open('packages/contracts/openapi.json'))['paths'];print('\n'.join(sorted(p)))"
scripts/check-standards
```

## Out of scope
- Implementing the business logic, worker, ffmpeg or SSE (those are the T-003-k tasks you're writing briefs for).
- Any UI.
- Real Modal/OpenRouter calls.

## Report
Write `docs/tasks/T-003-0/report.md` from `docs/templates/report.md`, then commit per the kickoff prompt (plain message, no trailers, include `.agent-logs/`).
