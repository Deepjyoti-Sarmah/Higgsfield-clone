# Design 002: Walking skeleton

**Spec:** `docs/specs/002-walking-skeleton/spec.md`

## API contract
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| GET | `/api/health` | — | `HealthResponse {status, database}` | 503 `{status:"degraded", database:"down"}` |
| POST | `/api/v1/auth/guest` | — | `UserResponse {id, is_guest, display_name, created_at}` + sets `session` cookie | 500 |
| GET | `/api/v1/me` | cookie `session` | `UserResponse` | 401 |
| GET | `/*` | — | built SPA `index.html` / static assets | — |

- **Session cookie:** `session` holds a JWT (HS256, `sub`=user id, `exp`=30 days). Flags: `httpOnly`, `Secure` (off only when `ENV=local`), `SameSite=Lax`, `Path=/`.
- **Contract flow:** `packages/contracts/openapi.json` is exported by `scripts/export-openapi`. The web client types are generated from it (`openapi-typescript`), and calls go through `openapi-fetch`.

## Data
- Table `app_user`: `id uuid pk default gen_random_uuid()`, `is_guest bool not null`, `display_name text`, `created_at timestamptz default now()`.
- Migration: `0001_create_app_user` (Alembic, async engine).

## Flow
1. The browser loads `/` and gets the SPA from FastAPI's static mount.
2. The SPA calls `GET /api/v1/me`. A 401 means the signed-out shell is shown.
3. On "Continue as guest", `POST /api/v1/auth/guest` runs: the service inserts `app_user` (one transaction), signs the JWT, and the router sets the cookie.
4. The SPA stores nothing itself; it refetches `me` and renders the header label.
5. The worker process (`APP_ROLE=worker`) opens the DB and logs `worker heartbeat` every 10s. The claim loop arrives in spec 004.

## Files (≤200 lines each)
| File | New/Edit | Responsibility |
|---|---|---|
| `docker-compose.yml` | New | local Postgres 17 + MinIO for dev/tests |
| `.env.example` | New | every env var name, no values |
| `Dockerfile` | New | build SPA (node) → Python image serving API + static; `APP_ROLE` picks api/worker |
| `railway.json` | New | Dockerfile build + healthcheck `/api/health` |
| `apps/api/pyproject.toml` | New | deps, ruff/mypy/pytest config |
| `apps/api/app/settings.py` | New | typed env config (pydantic-settings) |
| `apps/api/app/db.py` | New | async engine + `get_session` dependency |
| `apps/api/app/main.py` | New | `create_app()`: routers + SPA static mount |
| `apps/api/app/routers/health.py` | New | health endpoint |
| `apps/api/app/routers/auth.py` | New | guest + me endpoints, cookie set/read |
| `apps/api/app/services/session_tokens.py` | New | sign/verify session JWT |
| `apps/api/app/services/guest_accounts.py` | New | create guest user use case |
| `apps/api/app/repositories/users.py` | New | insert/get `app_user` |
| `apps/api/app/models/user.py` | New | SQLAlchemy `AppUser` |
| `apps/api/app/schemas/user.py` | New | `UserResponse`, `HealthResponse` |
| `apps/api/app/worker.py` | New | worker entrypoint (heartbeat) |
| `apps/api/migrations/…` | New | Alembic env + `0001_create_app_user` |
| `apps/api/tests/test_health.py`, `test_guest_session.py` | New | AC-1, AC-3, AC-4 against compose Postgres |
| `scripts/export-openapi` | New | write `packages/contracts/openapi.json` |
| `apps/web/…` (Vite React TS) | New | `ui/` (Button, AppShell), `features/session/` (useSession, GuestButton), `api/client.ts` |
| `apps/gpu/ltx_spike.py` | New | Modal function: LTX-2.5 distilled image→video → R2 |

## Reused
- Nothing yet (first code). This slice sets the patterns later specs reuse: `get_session`, the `session_tokens` service, `ui/Button`, `api/client`.

## Risks
- **Python version:** asyncpg/pydantic wheels on Python 3.14. Mitigation: pin 3.12 via `uv python`.
- **Railway Dockerfile builds** need the SPA build stage. Mitigation: test `docker build` locally first (T-002-3).
- **LTX-2.5 in Diffusers:** pipeline class and VRAM on Modal are unverified. The spike exists to find out.
