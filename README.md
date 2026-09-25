# Reel & Still

A small studio for short films. Make a still, animate it into a clip, then cut two to six clips into one
sequence — all in one workspace. It is one origin: a React SPA served by FastAPI, an append-only credit
ledger in Postgres, presigned uploads to S3/R2, and a worker that claims steps with leases and calls real
model backends (FLUX.1-schnell for images, LTX-2.5 for video, ffmpeg for sequence stitching), each with a
labelled fallback that never pretends a model ran.

| | |
|---|---|
| **Live:** | **https://api-production-8afc.up.railway.app** — Railway + Neon Postgres (UNPOOLED DSN) + Cloudflare R2. Guest auth, presigned uploads, image + video generation (720p h264 faststart mp4 + poster in R2), sequence stitching, SSE updates, credits with a visible ledger, and `/v/{id}` share pages. |
| **Repo:** | **https://github.com/Deepjyoti-Sarmah/Higgsfield-clone** — public, `main` in sync. |
| **Status:** | `docs/STATUS.md` — what works, what's broken, what hasn't started |
| **Plan:** | `docs/PLAN.md` — milestones, task board, role assignments |
| **Runbook:** | `docs/RUNBOOK.md` — operating costs, guardrails, and procedures |

## What it does

- Guest sign-in with an httpOnly JWT cookie; the credit balance is `SUM(ledger)`, never stored on the user.
- The studio (`/studio`) is one screen: a rail grouped by day, a stage for the selected item or live job,
  and three composer tabs — **Still**, **Clip**, **Sequence**.
- A still can be sent straight into Clip create (**Animate this**) with no download or re-upload.
- Sequences stitch 2–6 clips with cut / crossfade / fade-to-black transitions and optional music
  (audio/mpeg, audio/mp4, audio/wav up to 10 MB) into one 1280×720 mp4, for 1 credit.
- Every result captions its backend; a placeholder or fallback result is labelled as such.
- Uploads go straight to S3-compatible storage (MinIO locally, Cloudflare R2 in production) via presigned URLs.
- A worker claims steps with `FOR UPDATE SKIP LOCKED`, leases them, and calls the model adapter; the
  browser follows progress over SSE with a 5-second polling fallback.
- The share page `/v/{id}` server-renders Open Graph tags and plays all three job kinds signed out.

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
   +-- Postgres: user - asset - preset - job - job_step (queue) - job_sequence_clip - ledger
   +-- S3/R2: media via presigned URLs
   v
Worker (same image, APP_ROLE=worker): claim - lease - submit - callback
   v
Adapters: modal (FLUX.1-schnell images, LTX-2.5 video) | openrouter (paid budget)
          | ffmpeg (sequences) | labelled fallback (placeholder / local-motion)
```

One Docker image runs both roles (`APP_ROLE=api` or `worker`). See `docs/DECISIONS.md` for why — including
D-015 (images are real; the placeholder is a labelled fallback), which supersedes D-014.

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

Free end-to-end smokes (never need paid generation):

```sh
scripts/smoke-generation http://localhost:8000    # upload → video job → SSE → outputs → credits
scripts/smoke-sequence  http://localhost:8000     # 2 clips → crossfade sequence → stitch → ledger
```

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

## How agents work in this repo

This codebase is built by a multi-agent workflow, model- and tool-agnostic (see `docs/DECISIONS.md` D-008):

- [`AGENTS.md`](AGENTS.md) — the operating rules every agent reads first: the truth hierarchy, the
  definition of done, hard rules, and the task-packet interface (`brief.md` → `report.md`).
- [`docs/playbooks/multi-harness.md`](docs/playbooks/multi-harness.md) — how any harness claims a task,
  works it, and submits it, with prompts and responses captured in `.agent-logs/`.
- [`docs/tasks/`](docs/tasks/) — the task board: one folder per task packet, with status, thread,
  verify log and report. `docs/tasks/T-NNN-k/brief.md` is the whole interface between agents.

A reviewer that is a *different model* from the implementer re-runs the verify command before a task merges.

## Repo map

```
apps/web/            Vite + React + TS SPA (served by FastAPI as static files: one origin)
apps/api/            FastAPI (api + worker entrypoints, one image)
apps/gpu/            Modal app (FLUX.1-schnell images, LTX-2.5 video)
packages/contracts/  openapi.json -> generated TS client
docs/                plan, status, decisions, standards, specs, tasks, research, playbooks, templates, architecture
scripts/             agent-run, check-standards, check-links, export-openapi, install-hooks, smoke-generation, smoke-sequence
.agent-logs/         captured prompts/responses: committed, never edited by hand
Dockerfile           one image for api + worker (web build baked in)
docker-compose.yml   local Postgres + MinIO
railway.json         deploy config (health check: /api/health)
```

## Origin

Started as a Higgsfield rebuild for an assignment; redesigned as its own product in spec 010.
