# Runbook: deploy (Railway + Neon + R2 + Modal)

The account steps need a human (the user). Everything after "Hand over" can be done by an agent.
Never paste secret values into chat, docs or commits. Put them only in Railway variables, Modal secrets or a local `.env.local` (gitignored).

## 1. Accounts and logins (human)
| Service | Do this | Gives us |
|---|---|---|
| GitHub | `gh auth login` (the current keyring login is broken), then create a **public** repo | the repo URL for the hand-in and for Railway deploys |
| Neon | create a project, database `higgsfield`, copy the **pooled** connection string | `DATABASE_URL` |
| Cloudflare R2 | create bucket `higgsfield-media`, an API token with Object Read & Write, enable the public `r2.dev` URL | `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET`, `S3_PUBLIC_BASE_URL` |
| Railway | `npm i -g @railway/cli && railway login` | the CLI session |
| Modal | `uv tool install modal && modal token new` (opens a browser) | a Modal token on this machine |

Handy in Claude Code: type `! railway login` or `! modal token new` so the output lands in the session.

## 2. Hand over (human → agent)
Tell the agent "credentials are set". Put the values in:
- **Railway variables**, on both services: `ENV=production`, `DATABASE_URL`, `SESSION_SECRET` (`openssl rand -hex 32`), and the `S3_*` values.
- **Modal secret:** `modal secret create r2 R2_ENDPOINT_URL=… R2_ACCESS_KEY_ID=… R2_SECRET_ACCESS_KEY=… R2_BUCKET=…`

## 3. Railway services (agent, from the repo root)
```
railway init                      # or `railway link` to an existing project
railway up --service api          # Dockerfile build; healthcheck /api/health (railway.json)
railway variables --service worker --set APP_ROLE=worker
railway up --service worker
railway domain --service api      # public URL = the live link
```
- The worker has no HTTP port: turn **off** its healthcheck in the service settings, because `railway.json` sets one for `api`.
- The API runs `alembic upgrade head` on boot (`apps/api/entrypoint.sh`). Keep `api` at 1 replica until migrations move into a release step.

## 4. Verify (agent)
```
curl -s https://<live>/api/health                  # {"status":"ok","database":"ok"}
curl -s -o /dev/null -w '%{http_code}\n' https://<live>/api/v1/me   # 401
railway logs --service worker | grep heartbeat
modal run apps/gpu/ltx_spike.py --image <public image url> --prompt "slow dolly in"
```
Then run `docs/playbooks/verify-slice.md` for spec 002, and record the live URL in `docs/STATUS.md` and `README.md`.
