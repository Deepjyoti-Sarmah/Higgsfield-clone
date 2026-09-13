# Higgsfield (clone)

A rebuild of [higgsfield.ai](https://higgsfield.ai) — AI image and video generation — built in a 24-hour window.
Guests get credits, upload media, queue an image/video job, watch progress over SSE, and share the result.

| | |
|---|---|
| Live | TODO: add the deployed URL |
| Repo | TODO: add the repository URL |
| Status | `docs/STATUS.md` — what works, what's broken, what hasn't started |
| Plan | `docs/PLAN.md` — milestones, task board, role assignments |

## What it does

- Email/guest sign-in with an httpOnly JWT cookie; credit balance comes from an append-only ledger.
- Uploads go straight to S3-compatible storage (MinIO locally, R2 in production) via presigned URLs.
- `POST /api/v1/jobs` validates, holds credits, inserts the job + step, and returns `202` in one transaction.
- A worker claims steps with `FOR UPDATE SKIP LOCKED`, leases them, and calls a model adapter.
- The browser follows progress over SSE (with a 5s polling fallback) and loads the finished asset.

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

## Local development

Prerequisites: Docker, [uv](https://docs.astral.sh/uv/), Node 24, npm.

```sh
cp .env.example .env.local                              # names only; never commit values
docker compose up -d --wait db                          # Postgres on :5432 (and MinIO on :9000)
uv --directory apps/api sync                            # create apps/api/.venv
uv --directory apps/api run alembic upgrade head        # apply migrations
uv --directory apps/api run uvicorn app.main:app --reload   # API on http://localhost:8000

npm --prefix apps/web install
npm --prefix apps/web run dev                           # Vite dev server (proxies /api to :8000)
```

Set `GENERATION_BACKEND=mock` (the `.env.example` default) so no paid generation runs locally.
Generated API client: `npm --prefix apps/web run gen:api` regenerates it from `packages/contracts/openapi.json`.

Checks before you commit:

```sh
scripts/check-standards                                 # file/comment size rules (docs/STANDARDS.md)
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck
```

## Repo map

```
apps/web/            Vite + React + TS SPA, served by FastAPI as static files (one origin)
apps/api/            FastAPI: routers, services, repositories, models, migrations, tests
apps/gpu/            Modal app: LTX-2.5 (video), LLaDA-Image
packages/contracts/  openapi.json -> generated TS client
docs/                SPEC/STATUS/PLAN/DECISIONS/STANDARDS, specs, tasks, research, playbooks, templates
scripts/             agent-run, check-standards, export-openapi, install-hooks
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
