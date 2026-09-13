# Brief T-033: Guardrails + real-AI cutover (they ship together)

**Role:** implementer (strongest model) · **Blocks:** nothing may enable a paid GPU on the public URL before this lands

## Problem
The live site currently generates fake video (`local-motion` ffmpeg) because turning on the real Modal backend today would be unsafe:
- **No rate limiting anywhere.** Not per IP, not per user.
- **`paid_budget_cents` is decorative** — defined in `apps/api/app/settings.py`, read by nothing.
- **Infinite free GPU:** clearing cookies mints a fresh guest with a 60-credit `GRANT` (`app/services/guest_accounts.py`). A loop drains the Modal balance.
- **Unlimited fake top-ups:** `TOPUP_CREDITS = 100` with no cap.

## Goal
A stranger can use the public link, get **real AI video**, and cannot break it or drain the account.

## Part A — guardrails (must land first, in the same commit)
1. **Per-IP guest cap.** In `app/routers/auth.py` → `start_guest_session`, count guests issued from this IP today and refuse over the cap with **429**.
   - Store a **hash** of the IP (`sha256(ip + session_secret)`), never the raw address. Read it from `X-Forwarded-For` (Railway sits behind a proxy; uvicorn already runs with `--proxy-headers`).
   - New table + migration `0006`, repository + service, following the existing layering.
   - Default cap: `GUEST_PER_IP_DAILY = 5` in `app/domain/credit_rules.py`.
2. **Per-user daily generation cap.** In `create_job` (`app/services/job_creation.py`) and `create_image_job` (`app/services/image_job_creation.py`): count the user's jobs in the last 24h, refuse over `USER_DAILY_JOBS = 10` with **429**.
3. **Enforce the global budget.** Before a paid backend runs, sum today's paid spend; over `paid_budget_cents` → refuse new paid jobs with **429** and a clear message. Never call the GPU when over budget.
4. **Cap top-ups** at `TOPUP_DAILY_LIMIT = 2` per user per day.
5. Every refusal returns a typed error body the UI can render — no bare 500s.

## Part B — cutover to real AI
6. **Record which backend produced each job.** Add `generated_by` (text, nullable) to `job`, set it at completion, and expose it on `JobResponse`. **This is a deliberate contract change** — regenerate `packages/contracts/openapi.json` and say so in the report.
7. **Default `GENERATION_BACKEND=modal`** with automatic fallback to `local-motion` on `BackendNotConfiguredError`, timeout, or GPU error — the job still succeeds rather than failing the visitor.
8. **Label it honestly in the UI.** A result shows **"AI video"** when `generated_by == "modal"` and **"Motion preview"** when it fell back to `local-motion`. Never present ffmpeg output as AI. One badge component, used on the result view and the library row.
9. **Kill switch** stays: setting `GENERATION_BACKEND=local-motion` disables all paid calls.

## Allowed files
- `apps/api/app/domain/credit_rules.py`, `app/settings.py`, `.env.example`
- `apps/api/app/routers/{auth,jobs,image_jobs,credits}.py`
- `apps/api/app/services/{job_creation,image_job_creation,guest_accounts,credits,generation_runs,step_completion,job_views}.py`
- `apps/api/app/repositories/` (new rate-limit repository, jobs)
- `apps/api/app/models/`, `apps/api/migrations/versions/0006_*.py`
- `apps/api/app/schemas/jobs.py`, `packages/contracts/openapi.json`
- `apps/api/tests/**`
- `apps/web/src/features/create-video/ResultView.tsx`, `apps/web/src/features/library/`, `apps/web/src/ui/` (the badge only)

## Must reuse
- `InsufficientCreditsError` shape in `job_creation.py` for the new typed refusals.
- `lock_user_row` for anything that reads-then-writes a balance.
- `select_model_adapter` in `app/adapters/backend_selection.py` for the fallback — do not add a second selection path.
- The existing `ModalAdapter`; do not change `model_adapter.py`.

## Acceptance checks
- [ ] 6 guest creations from one IP → the 6th returns 429
- [ ] 11 jobs in 24h → the 11th returns 429
- [ ] With `paid_budget_cents` exhausted, no Modal call is made (assert the adapter is never invoked)
- [ ] 3rd top-up in a day → 429
- [ ] A Modal failure produces a successful job with `generated_by="local-motion"` and the UI shows "Motion preview"
- [ ] A real Modal run shows "AI video"
- [ ] Raw IPs appear nowhere in the DB or logs
- [ ] `openapi.json` regenerated; the diff contains only `generated_by`

## Verify command (paste full output in report.md)
```
docker compose up -d --wait db minio && docker compose run --rm minio-init
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --stat packages/contracts/openapi.json
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run build
scripts/check-standards
```

## Out of scope
- Images on our GPU (T-017), observability (T-034), Railway env changes (the human sets `MODAL_ENDPOINT_URL` + `MODAL_WEBHOOK_SECRET`).

## Report
`docs/tasks/T-033/report.md`. Note the contract change explicitly. One commit, plain message, no attribution trailers, include `.agent-logs/`.
