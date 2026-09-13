# Runbook: local development

Everything here runs on one machine. The source of truth for ports and services is `docker-compose.yml`;
for env names it is `.env.example`. Deploying is a separate runbook: `docs/runbooks/deploy.md`.

## Prerequisites

| Tool | Why | Check |
|---|---|---|
| Docker + Compose v2 | Postgres and MinIO | `docker compose version` |
| [uv](https://docs.astral.sh/uv/) | Python env and commands for `apps/api` | `uv --version` |
| Node 24 + npm | `apps/web` (Vite + React) | `node --version` |

## First run

```sh
cp .env.example .env.local                          # names only; never commit values
scripts/install-hooks                               # git config core.hooksPath .githooks

docker compose up -d --wait db minio                # Postgres :5432, MinIO :9000 (console :9001)
docker compose run --rm minio-init                  # creates the `media` bucket

uv --directory apps/api sync                        # creates apps/api/.venv
uv --directory apps/api run alembic upgrade head    # applies migrations

npm --prefix apps/web install
```

Then run the two dev servers in separate terminals:

```sh
uv --directory apps/api run uvicorn app.main:app --reload    # http://localhost:8000
npm --prefix apps/web run dev                                # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000` (`apps/web/vite.config.ts`), so the browser
only ever talks to `:5173`. MinIO's web console is at `http://localhost:9001` (`minioadmin` / `minioadmin`).

Keep `GENERATION_BACKEND=mock` from `.env.example` for local work. It makes generation instant and free;
`modal` and `openrouter` are placeholders and paid calls must never run in tests.

## Day-to-day

```sh
docker compose up -d --wait db minio    # after a reboot
uv --directory apps/api run alembic upgrade head
scripts/install-hooks                   # only if core.hooksPath is unset
```

## Checks before you commit

```sh
scripts/check-standards                 # file/comment size rules (docs/STANDARDS.md)
scripts/check-links                     # markdown links point at real files
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
```

`scripts/install-hooks` makes `git commit` run the standards check, plus ruff for staged `apps/api`
files and the web linter for staged `apps/web` files. Bypass it only in an emergency (`--no-verify`),
and say why in the commit body or the report.

Regenerate the typed API client after any schema change:

```sh
scripts/export-openapi                                  # writes packages/contracts/openapi.json
npm --prefix apps/web run gen:api                       # regenerates src/api/generated/schema.d.ts
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `docker compose up` fails on port 5432 | a local Postgres already listens there | stop it, or change the `db` port mapping and `DATABASE_URL` together |
| `/api/health` returns 503 | API can't reach the database | `docker compose ps`; confirm `DATABASE_URL` matches the `db` service |
| `alembic upgrade head` fails to connect | Postgres not up yet | `docker compose up -d --wait db` waits for the healthcheck |
| Uploads 500 / bucket errors | `media` bucket missing | `docker compose run --rm minio-init` |
| `npm --prefix apps/web run gen:api` produces stale types | schema changed, client not regenerated | run `scripts/export-openapi` first, then `gen:api` |
| `git commit` blocked by `check-standards` | a file is over 200 lines, or a comment block is over 3 lines | split the file or shorten the comment (`docs/STANDARDS.md`) |
| Tests hit a real backend | `GENERATION_BACKEND` not `mock` | `export GENERATION_BACKEND=mock`; tests must not use paid routes |

## Clean slate

```sh
docker compose down -v                  # -v drops the Postgres volume and MinIO data
docker compose up -d --wait db minio
docker compose run --rm minio-init
uv --directory apps/api run alembic upgrade head
```
