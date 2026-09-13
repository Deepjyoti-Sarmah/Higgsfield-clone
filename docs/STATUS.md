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
| Standards check (file ≤200 lines, comment block ≤3 lines) | `scripts/check-standards` | passes on the repo; a planted 205-line file with a 4-line comment fails with exit 1 | 2026-09-13 01:18 |

## BROKEN / KNOWN ISSUES
| What | Where | Impact | Next step |
|---|---|---|---|
| First session log has a response but no prompt | `.agent-logs/2026-09-12_23-39-23_26732883-*.md` | cosmetic; hooks were installed mid-session | leave as is (append-only); explained in `CAPTURE-TEST.md` |
| Codex account out of quota until 2026-09-30 | `.agent-logs/*codex_T-000-4.md` (response is the quota error) | no real non-Claude agent answer yet; the wrapper itself works | use `openrouter:<model>` once `OPENROUTER_API_KEY` is set, or another CLI |
| First Codex run hung for 180s (stdin left open), so only its PROMPT was logged | same log file, entry 1 | cosmetic | fixed: stdin closed, `AGENT_RUN_TIMEOUT` logs timeouts as a response |
| `gemini`, `aider` not installed; `OPENROUTER_API_KEY` not set | — | only Claude Code and Codex are usable as agents right now | install/set when needed |

## NOT STARTED
- Product research (`docs/research/`): waiting on screenshots
- apps/api, apps/web, apps/gpu, packages/contracts
- Deploy (Railway + Neon + R2), Modal spike
