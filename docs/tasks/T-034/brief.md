# Brief T-034: Observability, load test, and the operating/cost page

**Role:** implementer (strong model) · **After T-033 + T-017 are live**

## Problem
Two self-deployed models now serve real traffic on a public URL, but:
- `/api/health` only checks the database. R2 and the generation backends are unchecked, so the endpoint can report `ok` while every generation fails.
- Logging is unstructured (`logging.basicConfig` with a plain format in `apps/api/app/worker.py`). Job ids aren't consistently attached, so a failed generation can't be traced.
- Nobody has run two jobs at once. Concurrency behaviour under load is unknown.
- The unit economics exist only in task reports, not anywhere a reader will find them.

## Goal
Prove the thing is operable: you can tell when it's broken, you know what it does under load, and you can say what it costs.

## Part A — health that means something
Extend `apps/api/app/routers/health.py` + `app/services/system_health.py`:
- Keep `GET /api/health` cheap and unauthenticated (Railway's healthcheck uses it) — database only, current behaviour, unchanged.
- Add **`GET /api/health/deep`**: database, R2 (HEAD a known key via the existing `ObjectStorage`), the configured video backend and the configured image backend (reachability only — **never** run a paid generation), plus queue depth (queued `job_step` rows) and the oldest queued age in seconds.
- Return per-check `ok` / `degraded` / `down` with a duration in ms, and an overall status. 200 when healthy, 503 when any critical check is down.
- Add it to `packages/contracts/openapi.json` (**intended contract change** — regenerate and say so in the report).

## Part B — structured logs
- One JSON formatter used by both entrypoints (`app/main.py`, `app/worker.py`), controlled by `LOG_FORMAT=json|text` (default `json` in production, `text` locally).
- Every log line from a generation path carries `job_id`, `step_id`, `user_id`, `backend`, and `attempt` where they exist. Reuse the existing `logging.getLogger(__name__)` loggers — do not introduce a logging library.
- Log one line per job outcome with `duration_ms` and `generated_by`, so cost and latency are reconstructable from logs alone.
- **Never log** secrets, bearer tokens, presigned URLs with signatures, raw IPs, or prompts in full (truncate prompts to 80 chars).

## Part C — load test
- `scripts/load-test` (python, ≤200 lines, executable): N concurrent guests each run upload → create job → watch SSE to terminal, against `--base-url`, with `--jobs N` (default 5) and `--backend` so it can be pointed at the **free** `local-motion` path by default.
- Report per-job wall time, p50/p95, failures, and queue depth over time.
- Run it at 5 concurrent against the live URL on the free backend, and record the result. **Do not** run 5 concurrent paid GPU jobs.

## Part D — the operating page
`docs/RUNBOOK.md`, written for a reader who has never seen the repo:
- **Architecture in 10 lines** — API, worker, Postgres-as-queue, R2, two Modal models.
- **Unit economics table** with the measured numbers already in the task reports:
  | Path | Latency | Cost |
  |---|---|---|
  | Video (Modal LTX-2.5, H100) | 132–145 s | ~$0.16 / clip |
  | Images (Modal FLUX.1-schnell, H100) | 61.7 s warm, ~200 s cold | ~$0.05–0.06 warm, ~$0.18–0.25 cold / 4-image job |
  | Video fallback (local-motion, CPU) | ~2 s | $0 |
- **Guardrails in force** — per-IP guest cap, per-user daily cap, daily spend ceiling, top-up cap, with the current constants.
- **Operating procedures** — how to flip a backend, how to kill paid traffic (`GENERATION_BACKEND=local-motion`), how to read the queue depth, what to do when the GPU is cold, how to rotate a key.
- **Known limits** — single worker, cold starts, what would need to change to serve 100 concurrent users.
- Link it from `README.md`.

## Allowed files
- `apps/api/app/routers/health.py`, `app/services/system_health.py`, `app/schemas/` (health schema), `app/logging_setup.py` (new), `app/main.py`, `app/worker.py`, `app/settings.py`, `.env.example`
- `apps/api/app/services/{generation_runs,image_generation_runs,adapter_runs,step_claiming,lease_reaper}.py` (log lines only — **no behaviour changes**)
- `scripts/load-test` (new), `packages/contracts/openapi.json`
- `docs/RUNBOOK.md` (new), `README.md` (one link), `apps/api/tests/**`

## Must reuse
- `ObjectStorage` for the R2 check, `select_model_adapter` / `select_image_adapter` for backend identification, and the existing loggers.

## Acceptance checks
- [ ] `/api/health` unchanged and still cheap; `/api/health/deep` reports all five checks with durations
- [ ] Stopping MinIO locally turns the storage check `down` and the overall status 503
- [ ] `/api/health/deep` makes **zero** paid generation calls (assert the adapters are never invoked)
- [ ] Logs are valid JSON lines carrying `job_id` end to end for one real generation
- [ ] No secrets, presigned signatures, raw IPs or full prompts in any log line
- [ ] `scripts/load-test --jobs 5` completes against the live URL on the free backend, with p50/p95 recorded
- [ ] `docs/RUNBOOK.md` exists with the measured table and is linked from the README

## Verify command (paste full output in report.md)
```
docker compose up -d --wait db minio && docker compose run --rm minio-init
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --stat packages/contracts/openapi.json
curl -s localhost:8000/api/health/deep | python3 -m json.tool
scripts/load-test --base-url https://api-production-8afc.up.railway.app --jobs 5
scripts/check-standards
```

## Out of scope
- Sentry or any external monitoring service, metrics/Prometheus, alerting, autoscaling, paid load testing.

## Report
`docs/tasks/T-034/report.md` with the load-test numbers pasted. One commit, plain message, no attribution trailers, include `.agent-logs/`.
