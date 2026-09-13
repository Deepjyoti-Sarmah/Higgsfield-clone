# Capture Test — 8x assignment

## Tool and model
- **Tool:** Claude Code 2.1.270 (CLI, Linux)
- **Model:** `claude-opus-5` handles both planning and execution. No separate planner and no subagents.
- **Automatic mechanism:** yes. Claude Code lifecycle hooks.

## Mechanism
- Config file: `.claude/settings.json` (project level, committed)
- `UserPromptSubmit` runs `.claude/hooks/capture.py prompt`, which appends the verbatim prompt from the hook's stdin JSON.
- `Stop` runs `.claude/hooks/capture.py response`, which reads `transcript_path` from stdin and appends the final text the model produced after its last tool call in that turn. Thinking, tool calls and tool results are left out.
- Output: `.agent-logs/YYYY-MM-DD_HH-MM-SS_<session-id>.md`, one file per session. The front matter (`total_exchanges`, first and last prompt time, model list) is regenerated on every write. Entries are append-only.
- The script always exits 0, so a capture failure can never block the agent.
- All timestamps in the logs and in this document are UTC. Local time is IST (UTC+5:30).

## Log files the canaries landed in
- Session 1: `.agent-logs/2026-09-12_23-41-45_ff164378-08a5-4265-91b1-c4fc478b06c2.md` (interactive session, prompt typed by me)
- Session 2: `.agent-logs/2026-09-12_23-44-04_8cd59d0a-d4c7-4a66-b0b0-2b5cecf3e371.md` (a fresh session started non-interactively with `claude -p`. **The agent sent this prompt, not me.** It proves a brand-new session loads the hooks and captures on its own, but it isn't a canary I typed by hand.)

## Canary entries (raw)

Session 1 (`ff164378`), copied from the log:
```
[LOG_ENTRY type=PROMPT num=2 session=ff164378]
timestamp: 2026-09-12T23:42:07.829Z
model: claude-opus-5

CAPTURE TEST — 8x assignment, Deepjyoti Sarmah.
```
In the same file, RESPONSE #2 was appended at 23:42:29.425Z, when the turn ended.

Session 2 (`8cd59d0a`), copied from the log:
```
[LOG_ENTRY type=PROMPT num=1 session=8cd59d0a]
timestamp: 2026-09-12T23:44:04.718Z
model: claude-opus-5

CAPTURE TEST 2 — 8x assignment, Deepjyoti Sarmah. Reply with exactly: canary 2 received.


[LOG_ENTRY type=RESPONSE num=1 session=8cd59d0a]
timestamp: 2026-09-12T23:44:06.383Z
model: claude-opus-5

canary 2 received.
```

## What I tried first that did not work
- The assignment prompt itself was sent before any hook existed, so it isn't in `.agent-logs/`. It's only in Claude Code's local transcript.
- The first session's log (`26732883`) is therefore incomplete. It has RESPONSE #1 but no PROMPT, so its front matter shows `total_exchanges: 0` and blank prompt times. I've left the file as it was and haven't edited it after the fact.
- **A race between `Stop` and the transcript cut that response short.** The log holds only the turn's opening line ("I'll start with the capture setup…") and not the closing summary. In the transcript, the closing text row is timestamped 23:39:23.608Z, but the hook ran at 23:39:23.702Z, before that row had been written to disk. The script already retried while the transcript lagged, but its backup rule ("use the turn's last text block") returned the stale opening line immediately. Because that was non-empty, the retry loop never ran.
  - **Fix** in `.claude/hooks/capture.py`: `final_response` now returns the post-tool text and the backup text separately. The retry loop waits only for the post-tool text. After it gives up, the script tries the hook's `last_assistant_message`, and only then the backup.
  - **Checked** by replaying that session's real transcript cut off before the closing row, with the row added 1s after the hook started. The full closing summary was captured. A synthetic turn that really ends on a tool call still falls back to its last text block.
  - **Trade-off:** such a turn now waits for the full retry window (~5s, within the 15s hook timeout) before it's logged.
- I dry-ran the script against a real transcript with `AGENT_LOG_DIR` pointed at a scratch directory, and it worked first time. The dry run couldn't catch the race above, because by then the transcript had finished writing.
