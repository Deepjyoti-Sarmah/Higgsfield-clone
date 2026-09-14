# Runbook: operating the Higgsfield clone

For a reader who has never seen the repo. The live service is
https://api-production-8afc.up.railway.app (Railway `api` + `worker`, Neon Postgres, Cloudflare R2).

## Architecture in 10 lines
1. One origin: FastAPI serves the React SPA, `/api/*`, and `/v/{id}` share pages.
2. Guests get an httpOnly JWT cookie plus a one-time 60-credit grant; balance is `SUM(ledger)`.
3. Uploads go straight to R2 via presigned URLs; `complete` marks assets ready.
4. `POST /api/v1/jobs` validates, HOLDs credits, inserts job + step, NOTIFYs — one transaction.
5. The worker claims steps (`FOR UPDATE SKIP LOCKED`), renews the lease, runs the model adapter.
6. Video: LTX-2.5 on Modal (H100) with a free local-motion CPU fallback.
7. Images: FLUX.1-schnell on Modal with a placeholder fallback.
8. Progress streams over SSE (one LISTEN connection per replica, 5 s poll fallback).
9. Success SETTLEs the hold and stores mp4 + poster; failure RELEASEs (refunds).
10. `/api/health` is the cheap liveness probe; `/api/health/deep` checks every dependency.

## Unit economics (measured, not estimated)
| Path | Latency | Cost |
|---|---|---|
| Video (Modal LTX-2.5, H100) | 132–145 s | ~$0.16 / clip |
| Images (Modal FLUX.1-schnell, H100) | 61.7 s warm, ~200 s cold | ~$0.05–0.06 warm, ~$0.18–0.25 cold / 4-image job |
| Video fallback (local-motion, CPU) | ~2 s | $0 |

Sources: `docs/tasks/T-013/report.md`, `docs/tasks/T-017/report.md`.

## Guardrails in force
| Guardrail | Constant | Where |
|---|---|---|
| Guests per IP per day | 5 | `GUEST_PER_IP_DAILY` |
| Jobs per user per 24 h | 10 | `USER_DAILY_JOBS` |
| Top-ups per user per day | 2 × 100 credits | `TOPUP_DAILY_LIMIT`, `TOPUP_CREDITS` |
| Daily paid-spend ceiling | 500 cents ($5) | `paid_budget_cents` |
| Paid price: video / image | 25 c / 8 c per job | `PAID_VIDEO_COST_CENTS`, `PAID_IMAGE_COST_CENTS` |
| Credit price: video 20, images 10–15 | per preset / quality | `VIDEO_CREDIT_COST`, `image_rules` |

When the spend ceiling is hit, paid backends refuse new jobs and video falls back to local-motion.

## Operating procedures
- **Flip a backend:** set `GENERATION_BACKEND` (`local-motion`|`mock`|`modal`|`openrouter`) and/or
  `IMAGE_GENERATION_BACKEND` (`placeholder`|`mock`|`modal`) on the Railway `api` + `worker` services.
  Both must agree, otherwise creation-time guardrails and worker execution disagree.
- **Kill paid traffic now:** `GENERATION_BACKEND=local-motion` on both services. In-flight GPU calls
  finish; new jobs render free CPU clips. Same for images with `IMAGE_GENERATION_BACKEND=placeholder`.
- **Read the queue:** `GET /api/health/deep` → `checks.queue` (`depth`, `oldest_age_seconds`).
  Depth grows when the single worker is busy; age grows when a GPU call stalls.
- **GPU is cold:** first call after idle pays container boot + ~25 s model load. Hit the endpoint once
  before a demo; do not keep a GPU warm overnight ($3.95/h on H100).
- **Rotate a key:** R2/S3 keys live in Railway variables + the Modal `r2` secret; the GPU bearer lives in
  Railway `MODAL_WEBHOOK_SECRET` + the Modal `modal-auth` secret. Rotate both sides together, then
  redeploy. Never print a value into chat, docs, or commits.

## Known limits
- Single worker: one generation at a time; concurrent jobs queue (see the load-test numbers in
  `docs/tasks/T-034/report.md`). More workers = more concurrent claims, same DB.
- Cold starts dominate short demos; warm is 2–6× faster.
- 100 concurrent users need: more workers, a bigger (or second) GPU app, per-user rate limits below
  today's 10/day, and Postgres past a single Neon instance (LISTEN/NOTIFY fan-out per replica).
