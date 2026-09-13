# Higgsfield (clone)

A rebuild of [higgsfield.ai](https://higgsfield.ai) — AI image and video generation — built in a 24-hour window.
A visitor lands on a signed-out Explore page, picks one of 12 motion presets, drops in a photo and gets a
5-second video back in about a minute. It is one origin: a React SPA served by FastAPI, an append-only credit
ledger in Postgres, presigned uploads to S3/R2, and a worker that calls the model adapter.

| | |
|---|---|
| **Live:** | **https://api-production-8afc.up.railway.app** — Railway + your Neon Postgres. R2 storage keys are still pending, so browsing works but uploads/generation are not live yet |
| **Repo:** | TBD (public GitHub URL — `gh auth login` is still broken, see `docs/STATUS.md`) |
| **Status:** | `docs/STATUS.md` — what works, what's broken, what hasn't started |
| **Plan:** | `docs/PLAN.md` — milestones, task board, role assignments |

## What it does

- Guest sign-in with an httpOnly JWT cookie; the credit balance is `SUM(ledger)`, never stored on the user.
- Uploads go straight to S3-compatible storage (MinIO locally, Cloudflare R2 in production) via presigned URLs.
- `POST /api/v1/jobs` validates, holds credits, inserts the job + step and returns `202` in one transaction.
- A worker claims steps with `FOR UPDATE SKIP LOCKED`, leases them, and calls a model adapter.
- The browser follows progress over SSE (with a 5s polling fallback) and plays the finished clip.

## Architecture

Text version (kept current; wins over the drawings): [`docs/architecture/architecture.md`](docs/architecture/architecture.md).

```
Browser (React SPA, EventSource)
   |  same origin
   v
FastAPI  /api/*  REST + SSE, guest JWT cookie
         /*      built SPA static files
         /hooks/modal  generation callback
   |
   +-- Postgres: user - asset - preset - job - job_step (queue) - ledger
   +-- S3/R2: media via presigned URLs
   v
Worker (same image, APP_ROLE=worker): claim - lease - submit - callback
   v
ModelAdapter: modal | openrouter (paid budget) | mock (tests)
```

One Docker image runs both roles (`APP_ROLE=api` or `worker`). See `docs/DECISIONS.md` for why.

## Run it locally

Prerequisites: Docker + Compose v2, [uv](https://docs.astral.sh/uv/), Node 24 + npm.
Full runbook, including troubleshooting and a clean-slate reset: [`docs/runbooks/local-dev.md`](docs/runbooks/local-dev.md).

```sh
cp .env.example .env.local                          # names only; never commit values
scripts/install-hooks                               # git config core.hooksPath .githooks

docker compose up -d --wait db minio                # Postgres :5432, MinIO :9000 (console :9001)
docker compose run --rm minio-init                  # creates the `media` bucket

uv --directory apps/api sync                        # creates apps/api/.venv
uv --directory apps/api run alembic upgrade head    # applies migrations

npm --prefix apps/web install
```

Then the two dev servers, in separate terminals:

```sh
uv --directory apps/api run uvicorn app.main:app --reload    # API on http://localhost:8000
npm --prefix apps/web run dev                                # SPA on http://localhost:5173
```

Vite proxies `/api` to `:8000` (`apps/web/vite.config.ts`), so the browser only talks to `:5173`.
Keep `GENERATION_BACKEND=mock` (the `.env.example` default): generation is instant and free, and paid
`modal`/`openrouter` calls must never run in tests. Regenerate the typed client with
`scripts/export-openapi && npm --prefix apps/web run gen:api`.

Checks before you commit:

```sh
scripts/check-standards                 # file/comment size rules (docs/STANDARDS.md)
scripts/check-links                     # markdown links point at real files
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
```

## Repo map

```
apps/web/            Vite + React + TS SPA (served by FastAPI as static files: one origin)
apps/api/            FastAPI (api + worker entrypoints, one image)
apps/gpu/            Modal app (LTX-2.5 video, LLaDA-Image)
packages/contracts/  openapi.json -> generated TS client
docs/                plan, status, decisions, standards, specs, tasks, research, playbooks, templates, architecture
scripts/             agent-run, check-standards, check-links, export-openapi, install-hooks
.agent-logs/         captured prompts/responses: committed, never edited by hand
Dockerfile           one image for api + worker (web build baked in)
docker-compose.yml   local Postgres + MinIO
railway.json         deploy config (health check: /api/health)
```

## How agents work

This repo is the only memory between runs. `AGENTS.md` is the entry point and lists the hard rules;
read it before touching anything. In short: only touch the files your brief allows, never change the
API contract unless the task says so, never commit secrets, and never run paid generation in tests.

- Every task is a packet: `docs/tasks/T-NNN-k/brief.md` in, `report.md` next to it out.
- Prompts use `docs/templates/handoff-prompt.md` (strong models) or `docs/templates/handoff-prompt-small.md`
  (small/fast models); reports use `docs/templates/report.md`.
- Non-Claude tools run through `scripts/agent-run <tool> <task-id>`; Claude Code is captured by hooks.
- Chats are exported to `.agent-logs/` and committed; never edit a log by hand.
- Procedures live in `docs/playbooks/` (research, spec, task-run, verify-slice, handoff).
