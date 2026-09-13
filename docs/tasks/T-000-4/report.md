# Report T-000-4

**Agent / model / tool:** orchestrator · Claude Opus 5 · Claude Code (the canary agent was Codex CLI 0.151.0 via `scripts/agent-run`)
**Result:** PARTIAL (wrapper verified; no real answer from a non-Claude model yet)

## Files changed
- `scripts/agent-run`: new. Runs codex/gemini/aider or an OpenRouter model on a brief and logs the prompt + response with `capture.write_entry`
- `docs/tasks/T-000-4/brief.md`: canary brief

## Reused
- `log_path`, `write_entry` from `.claude/hooks/capture.py` (same log format as Claude Code sessions)

## Verify output
Run 1: `timeout 180 scripts/agent-run codex T-000-4` hit the timeout (exit 124). Only the PROMPT was logged.
- **Cause:** `codex exec` reads extra instructions from stdin, which was left open.
- **Fix:** `stdin=subprocess.DEVNULL`, plus `AGENT_RUN_TIMEOUT`, so a timeout is logged as the response.

Run 2: `AGENT_RUN_TIMEOUT=240 scripts/agent-run codex T-000-4` returned immediately. The log now has:
```
19:[LOG_ENTRY type=PROMPT num=1 session=codex_T-]
37:[LOG_ENTRY type=PROMPT num=2 session=codex_T-]
55:[LOG_ENTRY type=RESPONSE num=2 session=codex_T-]
...
ERROR: You've hit your usage limit. Upgrade to Plus to continue using Codex (https://chatgpt.com/explore/plus), or try again at Sep 30th, 2026 12:19 AM.
```

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- Codex quota blocks a real answer. Gemini and aider aren't installed, and `OPENROUTER_API_KEY` isn't set. Rerun with `scripts/agent-run openrouter:<model> T-000-4` once a key exists.
- Usage errors were checked: no args, unknown tool, missing brief. Each exits 1 with a message.

## Proposed STATUS.md line
| `agent-run` wrapper logs the prompt + response of a non-Claude CLI (including errors and timeouts) | `scripts/agent-run` | `scripts/agent-run codex T-000-4` → `.agent-logs/2026-09-13_01-19-16_codex_T-000-4.md` | 2026-09-13 01:24 |
