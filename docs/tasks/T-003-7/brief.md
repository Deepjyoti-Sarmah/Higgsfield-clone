# Brief T-003-7: End-to-end smoke of the generation core (local)

You are the **reviewer** for this one task. Use a **different model** from the one that implemented T-003-4 and T-003-5. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/003-generation-core/spec.md` (AC-1 … AC-8 end to end)
- Design: `docs/specs/003-generation-core/design.md` sections **API contract** (incl. SSE frames), **Storage**
- Contract: `packages/contracts/openapi.json` (all `/api/v1` paths)
- Reports to cross-check: `docs/tasks/T-003-{1..6}/report.md`

## Goal
Prove on a local stack (compose Postgres + MinIO, uvicorn api, one worker, `GENERATION_BACKEND=local-motion`) that a signed-out user can get a real motion video with correct credits and live progress, using only the HTTP API the browser will use.

## Allowed files (touch nothing else)
- `scripts/smoke-generation` (new, executable, Python 3 stdlib only: `urllib`, `json`, `subprocess`, `uuid`, `time`)
- `docs/tasks/T-003-7/report.md`
- The state files the definition of done requires (`docs/PLAN.md`, `docs/STATUS.md`, `docs/WORKLOG.md`, tick in `docs/specs/003-generation-core/tasks.md`)

## What the script does (`scripts/smoke-generation --base-url http://localhost:8000`), printing one `ok …` line per step and exiting 1 on the first failure
1. `GET /api/v1/presets` → ≥12, each `credit_cost` 20.
2. `POST /api/v1/auth/guest` (keep the cookie with `http.cookiejar`) → `GET /api/v1/credits` = 60.
3. Make a 1600×1000 jpg with `ffmpeg -f lavfi -i testsrc2=size=1600x1000:rate=1 -frames:v 1`.
4. `POST /api/v1/uploads` → PUT the bytes to `upload_url` with `upload_headers` → `POST /uploads/{id}/complete` → `ready`.
5. `POST /api/v1/jobs` (`dolly-in`, a fresh `idempotency_key`) → 202; repeat the same key → same `id`; credits = 40.
6. Open `GET /api/v1/jobs/{id}/events` and read frames until the stream closes (timeout 90s); the `status` sequence must start with `queued` and end with `succeeded`, with `running` in between.
7. `GET /api/v1/jobs/{id}` → `video_url`, `poster_url`; download both; `ffprobe` the mp4: h264, 1280×720, 120 frames, ~5.0s.
8. Two more jobs (credits 0), then a 4th → 402 with `balance` 0 and `required` 20.
9. A second guest → `GET /api/v1/jobs/{id}` of the first guest's job → 404.

## Acceptance checks
- [ ] The script passes end to end against the local stack
- [ ] Each AC-1 … AC-8 of spec 003 has a STATUS line citing a file path and this verify command (or the specific pytest file)
- [ ] Any mismatch between the running code and design/contract is written in the report (truth hierarchy: code + tests win, fix or report the lower source)

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db minio && docker compose run --rm minio-init
uv --directory apps/api run alembic upgrade head
(cd apps/api && GENERATION_BACKEND=local-motion uv run uvicorn app.main:app --port 8000 > /tmp/api.log 2>&1 &)
(cd apps/api && GENERATION_BACKEND=local-motion APP_ROLE=worker uv run python -m app.worker > /tmp/worker.log 2>&1 &)
sleep 3
scripts/smoke-generation --base-url http://localhost:8000
uv --directory apps/api run pytest -q
scripts/check-standards
pkill -f "uvicorn app.main:app"; pkill -f "python -m app.worker"
```

## Out of scope
- Fixing application code. If the smoke fails, write the failing step, logs (`/tmp/api.log`, `/tmp/worker.log`) and your diagnosis in the report and mark it BLOCKED/PARTIAL.
- The live deploy (a user placeholder), UI (spec 004).

## Report
Write `docs/tasks/T-003-7/report.md` using `docs/templates/report.md`, then follow the definition of done in `AGENTS.md` (commit per the kickoff prompt, plain message, no trailers, include `.agent-logs/`).
