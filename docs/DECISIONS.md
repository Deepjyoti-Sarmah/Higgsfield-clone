# DECISIONS: append-only

Format: `D-NNN · date · decision`. Then **Why**, and **Rejected** where it applies.
Never edit an old entry. To change a decision, add a new one that supersedes it.

## D-001 · 2026-09-13 · Postgres is the queue and the pub/sub
**Why:**
- `job` + `job_step` claimed with `FOR UPDATE SKIP LOCKED`, and enqueueing, the credit HOLD and NOTIFY happen in one transaction, so jobs can't get out of sync with credits.
- One stateful service.

**Rejected:** Redis/BullMQ (a second source of truth, and one more service to deploy).

## D-002 · 2026-09-13 · Generation: self-hosted open weights on Modal, OpenRouter as paid fallback
**Why:** low budget. Modal gives $30/month of free credits, scales to zero, H100 ≈ $3.95/h.
- **Video:** LTX-2.5 distilled fp8 (open weights, free under $10M ARR).
- **Images:** LLaDA-Image Turbo (6B, 4 steps). **Its licence isn't stated in the repo; verify before shipping.**
- **Fallback:**
  - Video: OpenRouter Seedance 2.0 Mini ($0.034/s).
  - Images: Seedream 4.5 ($0.04).

**Rejected:**
- fal.ai: the user prefers not to use it.
- InternLumina-U2: weights and licence "coming soon".
- OpenVDN: needs 8×B200.
- Viggle-Animate: 33B, 96GB, MiniMax community licence.
- InsightFace inswapper: non-commercial weights.
- HF ZeroGPU: 5 min/day of quota, long cold starts.

## D-003 · 2026-09-13 · Paid generation budget is a hard $5
**Why:** the public link means strangers spend real money.

**Guards:**
- A credit limit on the OpenRouter key.
- A server-side `PAID_BUDGET_CENTS=500` counter.
- Guests get 1 video + 3 images.
- A global daily cap.
- Pre-generated gallery previews.
- `GENERATION_BACKEND=mock` as a kill switch.

## D-004 · 2026-09-13 · Face swap is P1 and image-only
**Why:** a reference-image edit model (OpenRouter Nano Banana 2 Lite) costs ~$0.04 and needs no GPU. It requires a consent checkbox ("this is my face").

**Rejected:** video face swap (Viggle-Animate) for this window.

## D-005 · 2026-09-13 · Deploy on Railway + Neon + R2, one origin
**Why:**
- FastAPI serves the built SPA, `/api/*` and `/v/{id}` OG pages, so there's no CORS and no cross-site cookies, and no domain is needed.
- The worker is the same image with a different entrypoint.
- R2 has free egress.

**Rejected:** Cloudflare single origin (needs an owned domain), Fly.io (more setup).

## D-006 · 2026-09-13 · Cut from the MVP diagram: split worker pools and media workers (ffmpeg)
**Why:** provider outputs are already web-playable mp4s, so one worker pool is enough for demo load.

**Kept:** HOLD/SETTLE/RELEASE ledger, lease + reaper, idempotency key, separate worker process, ModelAdapter, `job_step` table, OG share page, one LISTEN connection per replica.

## D-007 · 2026-09-13 · Payments: credits with a fake top-up
**Why:** real checkout doesn't show product judgement in 24h. The ledger is real, only the money isn't.

## D-008 · 2026-09-13 · Agents are model- and tool-agnostic
**Why:** the user wants to use any model.
- Roles are defined by capability tier.
- The task packet (`brief.md` / `report.md`) is the whole interface.
- Every tool is captured via hooks or `scripts/agent-run`.

## D-009 · 2026-09-13 · Code standards are enforced by tooling
**Why:** rules nobody checks get broken by agents. See `docs/STANDARDS.md`.
- ≤200 lines per file.
- ≤3-line comments.
- Names that say what the code does.
- Layered API, ports only at real boundaries, rule of two for reuse.

## D-011 · 2026-09-13 · `pixovid/` is ignored
**Why:** it's an unrelated local project, and the user chose to ignore it.
- It's in `.gitignore`.
- Agents must not read, reuse or reference it.
- Everything here is built fresh under the approved plan.

## D-010 · 2026-09-13 · Commits carry no attribution trailers
**Why:** the user's instruction. No `Co-Authored-By` or session lines in commit messages.

## D-012 · 2026-09-13 · Scope locked as in `docs/research/product-map.md`
**Why:** the user approved the drafted verdicts.

- **P0:**
  - simplified Explore (hero, tool cards, preset gallery with Recreate)
  - Video create (image + ~12 presets + prompt, one default model)
  - one History/Assets library
  - credit cost on the Generate button
  - guest sign-in
  - `/v/{id}` share page
- **P1:** Image create, face swap (images), pricing with a fake top-up, model galleries.
- **P2:** model picker, community/profiles, search, upscale/inpaint/edit.
- **CUT:** Genjutsu, Edit/Motion/Extend video, audio/lipsync, MCP/plugin/Supercomputer, the studios, promo timers and discount toasts, notifications, Enterprise.

## D-013 · 2026-09-13 · The fake top-up is P0 and writes a `TOPUP` ledger row
**Why:**
- `docs/PLAN.md` § Scope and D-007 already put "credits with HOLD/SETTLE/RELEASE and a fake top-up" in the **P0 core loop**, while D-012's P1 list said "pricing with a fake top-up". The live board plus D-007 win: spec 008 is **P0**, and the orchestrator instruction for it says P0-simple.
- The ledger already pre-provisions the kind, so no migration is needed: `TOPUP` is in `ck_ledger_entry_kind` and in `domain/credit_rules.LedgerKind`, and `ck_ledger_entry_amount_sign` requires `amount > 0` with a NULL `job_id`.
- `GRANT` **cannot** be reused for a top-up: `uq_ledger_entry_guest_grant` is a partial unique index on `(user_id) WHERE kind = 'GRANT'`, and every guest already received that one-time welcome grant at account creation (`services/guest_accounts.py`). A second `GRANT` is a unique violation. A top-up is repeatable, job-less and positive — exactly `TOPUP`.

**Rejected:** a `GRANT` top-up (violates the one-time index); a new ledger kind or a migration (the kind already exists); a top-up cap (P1 — `POST /auth/guest` is already an unbounded faucet, so the cap would not close the hole that D-003's `PAID_BUDGET_CENTS` + `GENERATION_BACKEND=mock` already guard).
