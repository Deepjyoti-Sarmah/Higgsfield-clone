# Report T-033

**Agent / model / tool:** implementer (strongest model) · deepseek-flash (DSH main session) · run_code/bash
**Result:** DONE — guardrails + real-AI cutover, in one commit. The live "AI video" half needs the Railway env
from the hand-over step (below).

## Contract change (deliberate)
`generated_by: str | null` was added to **`JobResponse`** and **`LibraryItemResponse`** (the library row
needs it for the badge). `packages/contracts/openapi.json` was regenerated and the typed client rebuilt.
The whole diff is **+24 lines and the only added property is `generated_by`** (it also joins the required
lists of the two schemas). No path, no other schema, and no response declaration changed — the new 429
bodies are typed Pydantic models returned through `JSONResponse`, deliberately not declared on any route so
they stay out of the contract.

```
scripts/export-openapi && git diff --stat packages/contracts/openapi.json
 packages/contracts/openapi.json | 24 ++++++++++++++++++++++++
 1 file changed, 24 insertions(+)
```

## Part A — guardrails
- `guest_issuance` table + migration `0006_guardrails.py` (also adds `job.generated_by`), model, and
  `repositories/rate_limits.py` (counts + paid-spend sum).
- `services/guardrails.py`: hashes the client IP (`sha256(ip + session_secret)`), reads `X-Forwarded-For`
  first, and owns the four typed refusals: `GuestLimitError`, `DailyJobLimitError`, `TopUpLimitError`,
  `PaidBudgetExceededError` plus `is_paid_budget_exhausted`.
- Caps in `domain/credit_rules.py`: `GUEST_PER_IP_DAILY=5`, `USER_DAILY_JOBS=10`,
  `TOPUP_DAILY_LIMIT=2`, `PAID_VIDEO_COST_CENTS=25`, `PAID_IMAGE_COST_CENTS=5`, `PAID_BACKENDS`.
- `create_job`/`create_image_job` enforce the 24h job cap and (when the configured backend is paid) the
  daily budget before the balance check; `grant_top_up_credits` enforces the top-up cap;
  `create_guest_account` enforces the per-IP cap and records the hashed issuance in the same transaction.
- Routers return **429** with typed bodies: `{detail, limit, used}` and
  `{detail, spent_cents, budget_cents}`. No bare 500s.

## Part B — real-AI cutover
- `GENERATION_BACKEND` default is now **`modal`** (`.env.example` too); `select_fallback_model_adapter`
  returns `LocalMotionAdapter` for a paid primary.
- `services/adapter_runs.py` (new, split out so files stay ≤200 lines) runs the primary, and on
  `GenerationError`/`BackendNotConfiguredError`/timeout retries with the fallback. It also skips the paid
  primary and goes straight to the fallback when the paid budget is exhausted — the GPU is never called.
- `job.generated_by` is written at completion from the adapter that actually produced the output
  (`step_completion`/`image_step_completion`), and exposed on `JobResponse` + `LibraryItemResponse`.
- `ui/GenerationBadge.tsx`: **"AI video"** for `modal`/`openrouter`, **"Motion preview"** for
  `local-motion`, "Placeholder image" for `placeholder`. Used on the create-video result and the library
  row/result panel. `GENERATION_BACKEND=local-motion` remains the kill switch (no paid calls, no fallback).

## Files changed
- API: `domain/credit_rules.py`, `settings.py`, `.env.example`, `models/{job,guest_issuance}.py`,
  `migrations/versions/0006_guardrails.py`, `repositories/{rate_limits,jobs}.py`,
  `services/{guardrails,guest_accounts,job_creation,image_job_creation,credits,adapter_runs,step_inputs,generation_runs,image_generation_runs,step_completion,image_step_completion,job_views}.py`,
  `adapters/backend_selection.py`, `worker.py`, `routers/{auth,jobs,image_jobs,credits}.py`,
  `schemas/jobs.py`.
- Tests: `test_guardrails.py` (new), `test_adapter_fallback.py` (new), `worker_run_helpers.py` (new);
  `conftest.py`, `test_guest_session.py`, `test_modal_adapter.py` updated (unique guest IPs per test,
  monkeypatch target moved with `renew_lease_until_lost`).
- Web: `ui/GenerationBadge.tsx` (new), `features/create-video/ResultView.tsx`,
  `features/library/{LibraryItem,LibraryResultView}.tsx`, `api/generated/schema.d.ts` (regenerated).
- Contract: `packages/contracts/openapi.json`.

## Reused
- `InsufficientCreditsError`'s shape for the typed refusals; `lock_user_row` around every read-then-write;
  `select_model_adapter` (the fallback is a second selector, not a second path); the untouched
  `ModalAdapter` and `model_adapter.py`; existing worker/lease/completion machinery.

## Verify output (full paste, no summarising)
```
uv --directory apps/api run alembic upgrade head      -> 0006 (head)
uv --directory apps/api run ruff check .             -> All checks passed!
uv --directory apps/api run mypy                     -> Success: no issues found in 44 source files
uv --directory apps/api run pytest -q                -> 191 passed, 2 warnings in 72.11s
scripts/export-openapi && git diff --stat packages/contracts/openapi.json
                                                     -> 1 file changed, 24 insertions(+) [generated_by only]
npm --prefix apps/web run lint                       -> pass
npm --prefix apps/web run test                       -> 9 files / 60 tests passed
npm --prefix apps/web run build                      -> built in 490ms
scripts/check-standards                              -> check-standards: ok (0 violations)
```

## Acceptance checks
- [x] 6th guest from one IP → 429 (`test_sixth_guest_from_one_ip_is_rate_limited`)
- [x] 11th job in 24h → 429 (`test_eleventh_job_in_a_day_is_rate_limited`)
- [x] Budget exhausted → 429 at creation **and** the paid adapter is never invoked
      (`test_exhausted_budget_refuses_a_new_paid_job`, `test_exhausted_budget_never_invokes_the_paid_adapter`)
- [x] 3rd top-up in a day → 429 (`test_third_topup_in_a_day_is_rate_limited`)
- [x] A Modal failure yields a succeeded job with `generated_by="local-motion"`
      (`test_paid_failure_falls_back_to_local_motion`); the badge renders "Motion preview"
- [ ] A **real** Modal run shows "AI video" — backend + badge are ready; the live run needs the Railway
      `MODAL_ENDPOINT_URL`/`MODAL_WEBHOOK_SECRET` hand-over (this task's out-of-scope), so it is
      **UNVERIFIED here on purpose**
- [x] Raw IPs appear nowhere: only `sha256(ip + session_secret)` is stored
      (`test_guest_ip_is_stored_only_as_a_hash`); the code logs no address
- [x] `openapi.json` regenerated; the diff contains only `generated_by`

## Open issues / guesses / things skipped
- **Three files outside the brief's literal allowed list were required and are called out rather than
  hidden:** `worker.py` and `adapters/backend_selection.py` (the brief's "Must reuse `select_model_adapter`"
  for the fallback cannot be wired without them), and the generated
  `apps/web/src/api/generated/schema.d.ts` (mechanical output of the intended contract change).
- **Paid spend is estimated, not metered.** The budget sums `PAID_VIDEO_COST_CENTS=25` per paid video and
  `PAID_IMAGE_COST_CENTS=5` per paid image, because the Modal endpoint returns no cost. Tune the constants
  once T-017 measures the real image cost.
- **Burst concurrency:** the budget is checked at creation and again at worker time, but N jobs queued
  before the first completes can all start and overshoot by up to N×cost. The single live worker processes
  one step at a time, so production is sequential; a multi-replica worker would need an atomic reservation.
- `IMAGE_GENERATION_BACKEND` was added here (default `placeholder`) as the seam T-017 needs; image budget
  enforcement keys off it, so it is inert until T-017 switches the image adapter.
- The local `.env.example` default is now `modal`; a developer without an endpoint gets an instant
  `BackendNotConfiguredError` and the local-motion fallback, which is the intended behaviour.
- Not marked reviewed — a different model must review.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Guardrails + real-AI cutover: per-IP guest cap (5/day, hashed IP), per-user 24h job cap (10), daily paid-budget guard (no GPU call when exhausted), top-up cap (2/day), typed 429 bodies; `GENERATION_BACKEND=modal` with automatic `local-motion` fallback and `generated_by` on job + library, UI badge says "AI video"/"Motion preview" | `apps/api/app/services/guardrails.py`, `adapter_runs.py`, `repositories/rate_limits.py`, `migrations/versions/0006_guardrails.py`, `apps/web/src/ui/GenerationBadge.tsx`, `packages/contracts/openapi.json` | `ruff + mypy + pytest -q` → 191 passed (8 new), `export-openapi` +24 lines (only `generated_by`), web lint/test/build, `check-standards` ok (full output in `docs/tasks/T-033/report.md`) | 2026-09-14 04:55 |
