# Playbook: multi-harness task protocol

Agents run in different harnesses (Claude Code, Codex, opencode, IDE chat) with no shared chat. The repo is the only shared memory. This page is the whole protocol: claim a task, work apart, verify the same way, submit for review.

## Lifecycle

| Move | Who | Command |
|---|---|---|
| `open` → `claimed` | implementer | `scripts/task claim` |
| `claimed` → `blocked` | implementer | `scripts/task say … QUESTION` |
| `blocked` → `claimed` | orchestrator | `scripts/task say … ANSWER` |
| `claimed` / `changes-requested` → `submitted` | implementer | `scripts/task submit` |
| `submitted` → `accepted` | reviewer | `scripts/task review … accept` |
| `submitted` → `changes-requested` | reviewer | `scripts/task review … changes` |

## Implementer steps

1. `scripts/task list`: pick an `open` task.
2. `scripts/task claim <TASK> --as <agent>@<harness>` (or `export TASK_AS=<agent>@<harness>` once, then skip `--as`).
3. `cd .worktrees/<TASK>`. The command prints the path. Work only here, only in the brief's allowed files.
4. Read `docs/tasks/<TASK>/brief.md` to the end before editing.
5. Do the work.
6. When blocked: `scripts/task say <TASK> QUESTION "…" --as <agent>@<harness>`. Read the answer with `scripts/task show <TASK>` (your branch copy of the thread goes stale).
7. `scripts/task verify <TASK>`: runs the brief's verify block, then `check-standards`, writes `verify.log`.
8. Write `docs/tasks/<TASK>/report.md`.
9. `scripts/task submit <TASK> --as <agent>@<harness> --transcript <file>`.

## Orchestrator / reviewer steps

1. `scripts/task show <TASK>`: brief, status, full thread.
2. Answer with `scripts/task say <TASK> ANSWER "…" --as <you>`.
3. Re-run verify yourself: `cd .worktrees/<TASK> && scripts/task verify <TASK>`.
4. `git diff main...task/<TASK>`. Review the branch.
5. `scripts/task review <TASK> accept|changes "…" --as <you>`. This never merges.
6. Merge on `main` with `git merge --no-ff task/<TASK>`, then do the definition-of-done updates there: tick `tasks.md`, update STATUS and WORKLOG, include `.agent-logs/`, plain message with no trailers.

## Transcript capture per harness

| Harness | How |
|---|---|
| Claude Code | Hooks capture automatically. Use `--as <model>@claude-code`, no `--transcript`. |
| Codex, Gemini, Aider, opencode | Run through `scripts/agent-run <tool> <TASK>`, pass its log file as `--transcript`. |
| Anything else (IDE chat, web UI) | Export the chat to a file, pass it as `--transcript`. No log file means not done. |

## Identity naming

`<model>@<harness>`, lowercase, no spaces: `deepseek-v3@opencode`, `gpt-5-mini@codex`, `sonnet-5@claude-code`.

## Rules

- Never edit `status`, `thread.md` or `BOARD.md` by hand. `scripts/task` owns them.
- Never commit on `main` yourself. The orchestrator merges.
- Never merge your own branch.
- The reviewer must be a different model from the implementer.

## Known limits

- Tests that use the shared dev database can race when two worktrees run pytest at once (see STATUS BROKEN). Run DB-backed verifies one at a time.
