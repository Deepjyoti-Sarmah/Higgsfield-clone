# Report T-002-4

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** PARTIAL — **Neon is wired + migrated + health-ok; the Modal token authenticates; R2 is the remaining blocker** (per the brief, the Modal spike was NOT deployed).

## Files changed
- `docs/tasks/T-002-4/report.md` (this file, new).
- `docs/STATUS.md`, `docs/WORKLOG.md` (one line each), `.agent-logs/` (session capture).
- **No source file was changed.** The Neon wiring needed no code change: the app already reads `DATABASE_URL` from `.env.local`.
- **No secret was committed.** `.env.local` and `.neon` are gitignored and untracked; nothing secret appears in this report or in any tracked file.

## Secrets handling (read this first)
- The brief said `.neon` holds "the Neon pooled connection string". It does **not**: it is a 106-byte **JSON object** (three short keys → short values, no `://`, no `@`, no `=`), i.e. Neon project/branch metadata, not a DSN. Its values were never printed; only structural facts (length, separators, masked shape) were inspected.
- The real **pooled** connection string was already present in the pre-existing, gitignored **`.env.local`** as `DATABASE_URL` (plus `DATABASE_URL_UNPOOLED` and `NEON_BRANCH`). Verified: scheme `postgresql`, host `*.neon.tech`, `-pooler` present, `sslmode` present; `git check-ignore` confirms `.env.local` and `.neon` are ignored and `git ls-files` confirms neither is tracked.
- No tracked file contains a credential. Every command output below was passed through a redactor (env values for Part A, token-shaped values for Part B) before it was written here.

## Verify output (full paste, no summarising)
```
### PART A — Neon (hosted Postgres)

$ uv --directory apps/api run alembic upgrade head
-> exit 0 (alembic.ini configures no logger, so success prints nothing)

$ uv --directory apps/api run python -c "<read alembic_version + preset rows>"
alembic_version: 0003
preset_count: 12
slugs: crash-zoom,dolly-in,dolly-out,handheld,ken-burns,orbit-push,pan-left,pan-right,slow-drift,spiral-in,tilt-up,whip-pan
distinct_credit_costs: [20]
host_is_neon: True
host_is_pooler: True
-> exit 0

$ curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8012/api/health
{"status":"ok","database":"ok"}
HTTP 200
$ curl -s http://127.0.0.1:8012/api/v1/presets  (count)
preset_count: 12
$ curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8012/api/v1/me  (signed out)
HTTP 401

### PART B — Modal

$ modal --version
modal client version: 1.5.5

$ modal config show   (token values redacted)
{
  "async_warnings": true,
  "build_validation": "error",
  "cuda_checkpoint_path": "<REDACTED>",
  "default_cloud": null,
  "dev_suffix": "",
  "disable_api_proxy": false,
  "environment": null,
  "force_build": false,
  "function_runtime": null,
  "function_runtime_debug": false,
  "heartbeat_interval": 15,
  "ignore_cache": false,
  "image_builder_version": null,
  "image_id": null,
  "log_format": "STRING",
  "log_pattern": null,
  "loglevel": "WARNING",
  "logs_timeout": 10,
  "max_throttle_wait": null,
  "oauth_client_id": null,
  "oauth_client_secret": null,
  "oauth_refresh_token": null,
  "override_headers": null,
  "payload_format": "pickle",
  "restore_state_path": "<REDACTED>",
  "runtime_perf_record": false,
  "sandbox_v2": null,
  "serve_timeout": null,
  "server_url": "<REDACTED>",
  "snapshot_debug": false,
  "strict_parameters": false,
  "sync_entrypoint": null,
  "task_id": null,
  "token_id": "<REDACTED>",
  "token_secret": "<REDACTED>",
  "traceback": false,
  "worker_id": null
}

$ modal app list   (proves the token authenticates against the Modal API)
                                        Apps                                    
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━
┃ App ID                    ┃ Description ┃ State ┃ Tasks ┃ Created at ┃ Stopped
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━
└───────────────────────────┴─────────────┴───────┴───────┴────────────┴────────
-> exit 0

$ modal secret list
                     Secrets                     
┏━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Name ┃ Created at ┃ Created by ┃ Last used at ┃
┡━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
└──────┴────────────┴────────────┴──────────────┘
-> exit 0  (EMPTY: no r2 secret exists)
```

## Answers

**1. Is Neon wired + migrated + health-ok? — YES.**
- Wiring: `apps/api` reads `DATABASE_URL` from the gitignored repo-root `.env.local` (`Settings` env_file `../../.env.local`), and `Settings.async_database_url` converts it to `postgresql+asyncpg` (with `sslmode` → `ssl`). No code change was needed.
- Migrated: `uv --directory apps/api run alembic upgrade head` exit 0; `alembic_version = 0003`.
- Seeded: `preset_count = 12` (`crash-zoom … whip-pan`), `distinct_credit_costs = [20]` — migration `0003` seeded the catalogue on Neon, not just locally.
- Health: `GET /api/health` → `{"status":"ok","database":"ok"}` HTTP 200 against Neon; `GET /api/v1/presets` → 12; `GET /api/v1/me` signed out → 401.
- Confirmed the connection really is the hosted pooled one: `host_is_neon: True`, `host_is_pooler: True` (booleans only, never the host or DSN).

**2. Does the Modal token authenticate? — YES.**
- `modal --version` → `modal client version: 1.5.5`; `modal config show` → exit 0 with `token_id` and `token_secret` present (both redacted here; Modal itself prints `token_secret` as `***`).
- `modal app list` → exit 0 and an empty app table. That is a **live authenticated API round-trip**, so the token is valid — and it also shows **no app has ever been deployed** on this account, so there is no endpoint to point the API at.

**3. What exactly is still missing for a real `GENERATION_BACKEND=modal` run? — four things, in order:**
1. **R2 (the blocker).** `apps/gpu/ltx_spike.py`'s `generate_clip` declares `secrets=[modal.Secret.from_name("r2")]` and uploads the clip with `R2_ENDPOINT_URL` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET`. `modal secret list` is **empty**, so the secret does not exist. Per the brief I stopped here and did not invent storage. Next step (human, in the R2 account): create bucket `higgsfield-media` + an Object Read & Write token + the public `r2.dev` URL, then
   `modal secret create r2 R2_ENDPOINT_URL=… R2_ACCESS_KEY_ID=… R2_SECRET_ACCESS_KEY=… R2_BUCKET=…`
2. **Deploy + smoke the spike.** `modal deploy apps/gpu/ltx_spike.py` (this creates the `ltx-weights` volume and builds the torch image), then `modal run apps/gpu/ltx_spike.py --image <public image url> --prompt "slow dolly in"`. This is the only step that actually proves a real clip; it is an H100 job, so it costs real (free-tier) credits. Record the deployed function reference as the endpoint.
3. **Point the API at it.** Set `MODAL_ENDPOINT_URL` (and `MODAL_WEBHOOK_SECRET`) in the API env — both are empty in `.env.example` and absent from `.env.local`.
4. **The adapter is still a stub — this is the biggest hidden gap.** `apps/api/app/adapters/modal_adapter.py` raises `BackendNotConfiguredError("modal backend not configured: set MODAL_ENDPOINT_URL")` when the endpoint is empty, and `GenerationError("modal backend not implemented yet")` even when it is set. So `GENERATION_BACKEND=modal` **cannot produce a video today regardless of R2**: design 003/D-002 kept the real remote adapters as placeholders outside that spec, and no task has implemented the call yet. There is also **no `/hooks/modal` route** in `apps/api/app` (grep found none), so the callback path from `docs/architecture/architecture.md` is unimplemented too.

## Open issues / guesses / things skipped
- **The deploy was deliberately skipped**, not failed: the brief says to stop when R2 is not configured, and a `modal deploy` would also create the `ltx-weights` volume as a side effect. `modal app list` being empty is the evidence that no endpoint exists.
- **The spike is unverified end to end and may need code changes.** It imports `LTX2Pipeline` and `diffusers.pipelines.ltx2.utils` from `git+https://github.com/huggingface/diffusers` at build time; `Lightricks/LTX-2.5-Diffusers` and those symbols were never exercised here. Expect the first real run to need fixes. It also asserts audio output (`audio[0]`) — unverified.
- **`.neon` should not be trusted as a DSN.** Whatever created it wrote metadata, not a connection string. The wiring works because `.env.local` has the real pooled URL; if that file is lost, `.neon` alone is not enough to reconnect.
- **`.gitignore` currently adds `.neon` but that edit is uncommitted** (made by a concurrent agent). Until it lands, `.neon` is only ignored in the working tree, not in `HEAD`. I did not commit it (not my change).
- **`docs/WORKLOG.md` had a concurrent uncommitted line** from another agent; only this task's appended line is staged from that file.
- Neon was connected over the **pooled** endpoint, which is right for the app, but Alembic ran over the pooler too. Neon's pooler is PgBouncer in transaction mode, which can bite on session-level DDL later; migrations ran clean here, but the unpooled `DATABASE_URL_UNPOOLED` is the safer choice if a future migration misbehaves.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Neon (hosted Postgres) wired: pooled `DATABASE_URL` loaded from gitignored `.env.local`, migrations applied (`0003`), 12 presets seeded on Neon, `/api/health` ok, `/presets` 12, `/me` 401 signed out | `apps/api/app/settings.py` (env wiring only; no code change), `.env.local` (gitignored) | `uv --directory apps/api run alembic upgrade head && uv --directory apps/api run uvicorn app.main:app --port 8012 & curl /api/health` -> `{"status":"ok","database":"ok"}` HTTP 200; `alembic_version=0003`, `preset_count=12`, `host_is_neon=True`, `host_is_pooler=True` (full output in `docs/tasks/T-002-4/report.md`) | 2026-09-13 13:23 |
