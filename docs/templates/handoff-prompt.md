# Handoff prompt: boilerplate for giving a task to ANY agent

A handoff has two parts:
1. **The brief:** `docs/tasks/<TASK_ID>/brief.md`, written from `docs/templates/delegation-brief.md`. It holds the whole task: links, allowed files, checks, verify command.
2. **The kickoff prompt** below, pasted into the agent (or sent automatically by `scripts/agent-run`). It's the same for every task; only the placeholders change.

## Kickoff prompt (copy, replace the `<…>` values, paste)
```
You are working in the git repository at <REPO_PATH>. You have no prior context; the repo is the only source of truth.

Your task packet is docs/tasks/<TASK_ID>/brief.md. Your role is <implementer | designer | reviewer | scout>.

Do this in order:
1. Read AGENTS.md completely.
2. `scripts/task claim <TASK_ID> --as <agent>@<harness>` and `cd` into the worktree it prints.
3. Work only in the worktree, only in the brief's allowed files. Follow docs/STANDARDS.md
   (≤200 lines per file, ≤3-line comments, names that say what the code does, reuse before writing new code).
4. If something is unclear, contradictory or blocked, `scripts/task say <TASK_ID> QUESTION "…" --as <agent>@<harness>` instead of guessing. Read answers with `scripts/task show <TASK_ID>`.
5. Run `scripts/task verify <TASK_ID>`.
6. Write docs/tasks/<TASK_ID>/report.md using docs/templates/report.md.
7. `scripts/task submit <TASK_ID> --as <agent>@<harness> --transcript <file>` (no `--transcript` for Claude Code).

Rules: never change files outside the brief, never edit old .agent-logs entries, never commit secrets, never commit on main, never merge your own branch.
Final reply: result (DONE / PARTIAL / BLOCKED), files changed, open issues.
```

## How to launch it (prompts and responses must end up in `.agent-logs/`)
| Tool | Launch | Capture |
|---|---|---|
| Claude Code (any Claude model) | `claude --model <model>` in the repo root, paste the kickoff prompt | automatic (project hooks); submit needs no `--transcript` |
| Codex CLI | `scripts/agent-run codex <TASK_ID>` | automatic (wrapper); pass its log file as `--transcript` |
| Gemini CLI | `scripts/agent-run gemini <TASK_ID>` | automatic (wrapper); pass its log file as `--transcript` |
| Aider + any OpenRouter model | `scripts/agent-run aider <TASK_ID>` (set the model in aider's config) | automatic (wrapper); pass its log file as `--transcript` |
| Text-only model (review, planning) | `OPENROUTER_API_KEY=… scripts/agent-run openrouter:<model-id> <TASK_ID>` | automatic (wrapper); it can't edit files, so it's only for reviewer/designer text output |
| Cursor / IDE chat / web UI | paste the kickoff prompt | **manual:** export the chat into `.agent-logs/<date>_<tool>_<TASK_ID>.md` and pass it as `--transcript` |

`scripts/agent-run` sends the brief itself as the prompt. Every brief starts with the same "read AGENTS.md first" instructions, so the kickoff prompt is only needed for tools that you paste into by hand.

## Writing a new brief (orchestrator)
1. `mkdir -p docs/tasks/<TASK_ID>` and copy `docs/templates/delegation-brief.md` → `brief.md`.
2. Fill in every section. **Allowed files** and **Verify command** must never be empty.
3. Write `docs/tasks/<TASK_ID>/status` containing `open`, run `scripts/task board`, and commit the brief, `status` and `BOARD.md` before handing off, so the agent starts from a clean tree.

## After the agent finishes (reviewer, on a different model)
1. Re-run the verify command yourself. Never trust the pasted output alone.
2. Check the diff against the spec's acceptance criteria and `docs/STANDARDS.md`.
3. Pass: set the PLAN status to DONE and tick `tasks.md`. Fail: write the issues into a new brief `<TASK_ID>-fix`.
