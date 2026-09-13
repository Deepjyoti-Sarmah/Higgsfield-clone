# STATUS: the live truth

A line is valid only if it has a **path** and a **verify command** (or a named manual check) with a date.
Keep it short: replace lines as things change instead of piling new ones up. History goes in `WORKLOG.md`.

## WORKS
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Prompt/response capture (Claude Code main session) | `.claude/hooks/capture.py`, `.claude/settings.json` | canary prompts in 2 sessions, see `CAPTURE-TEST.md` | 2026-09-12 23:44 |
| Stop-hook race fix (final text flushed after hook fires) | `.claude/hooks/capture.py` | replayed truncated transcript + late append, full text captured | 2026-09-12 23:45 |
| Subagent capture: delegation prompt (`DELEGATE`) + output (`SUBAGENT_RESPONSE`), tagged with the subagent's model | `.claude/hooks/capture.py` (`delegate`, `subagent`), `.claude/settings.json` | live: Haiku canary subagent logged in `.agent-logs/*ff164378*.md`; offline: synthetic transcript tests | 2026-09-13 01:23 |
| `agent-run` wrapper logs the prompt + response of a non-Claude CLI (including errors and timeouts) | `scripts/agent-run` | `scripts/agent-run codex T-000-4` → `.agent-logs/2026-09-13_01-19-16_codex_T-000-4.md` | 2026-09-13 01:24 |
| API skeleton: `GET /api/health` (200/503), `POST /api/v1/auth/guest` (httpOnly cookie), `GET /api/v1/me` (401 without/tampered cookie), worker heartbeat, migration `0001` | `apps/api/`, `packages/contracts/openapi.json` | `docker compose up -d db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run pytest -q` → 7 passed; ruff + mypy strict clean | 2026-09-13 02:05 (local only, not deployed) |
| Web shell: dark AppShell with 5-item nav, guest button (idle/loading/error), typed client from openapi.json | `apps/web/` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build` all pass (re-run by the reviewer) | 2026-09-13 02:40 (local) |
| Container image: web build → Python; `APP_ROLE=api` runs migrations + uvicorn and serves the SPA with deep links; `APP_ROLE=worker` logs a heartbeat | `Dockerfile`, `apps/api/entrypoint.sh`, `.dockerignore`, `railway.json` | `docker build -t hf-clone .`; `docker run --network host -e DATABASE_URL=postgresql://…localhost:5432/higgsfield hf-clone` → health 200, `/` + `/create/video` 200, guest 201, me 200; worker run → 2 heartbeats in 12s | 2026-09-13 01:50 (local) |
| Standards check (file ≤200 lines, comment block ≤3 lines) | `scripts/check-standards` | passes on the repo; a planted 205-line file with a 4-line comment fails with exit 1 | 2026-09-13 01:18 |
| Home "Create video" button uses `navigate("/create/video")` instead of nesting a `<button>` in a `<Link>` (valid HTML, one focus stop) | `apps/web/src/features/home/HomePage.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` all pass; `grep -n "<Link"` on the file prints nothing | 2026-09-13 01:55 |

## BROKEN / KNOWN ISSUES
| What | Where | Impact | Next step |
|---|---|---|---|
| First session log has a response but no prompt | `.agent-logs/2026-09-12_23-39-23_26732883-*.md` | cosmetic; hooks were installed mid-session | leave as is (append-only); explained in `CAPTURE-TEST.md` |
| Codex account out of quota until 2026-09-30 | `.agent-logs/*codex_T-000-4.md` (response is the quota error) | no real non-Claude agent answer yet; the wrapper itself works | use `openrouter:<model>` once `OPENROUTER_API_KEY` is set, or another CLI |
| First Codex run hung for 180s (stdin left open), so only its PROMPT was logged | same log file, entry 1 | cosmetic | fixed: stdin closed, `AGENT_RUN_TIMEOUT` logs timeouts as a response |
| `gemini`, `aider` not installed; `OPENROUTER_API_KEY` not set | — | only Claude Code and Codex are usable as agents right now | install/set when needed |
| Deploy + Modal are PLACEHOLDERS (user's decision 2026-09-13: the user sets up Railway/Neon/R2/Modal personally) | `docs/runbooks/deploy.md`, `railway.json`, `apps/gpu/ltx_spike.py` | no live URL yet; all features are built and verified locally until then | user follows the runbook, then tells the agent "credentials are set" |
| `gh` CLI login broken (keyring) | — | can't create the public GitHub repo from here | user: `gh auth login` |

## NOT STARTED
- Specs 003 (generation core) and 004 (Create video): briefs `docs/tasks/T-003-0`, `T-004-0` ready for handoff
- Specs 005–008: Library, Explore, Share page, Credits + top-up
- Live deploy + Modal spike (user placeholders, `docs/runbooks/deploy.md`)
