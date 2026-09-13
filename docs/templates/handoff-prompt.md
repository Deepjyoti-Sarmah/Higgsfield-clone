# Handoff prompt: boilerplate for giving a task to ANY agent

A handoff has two parts:
1. **The brief:** `docs/tasks/<TASK_ID>/brief.md`, written from `docs/templates/delegation-brief.md`. It holds the whole task: links, allowed files, checks, verify command.
2. **The kickoff prompt** below, pasted into the agent (or sent automatically by `scripts/agent-run`). It's the same for every task; only the placeholders change.

## Kickoff prompt (copy, replace the `<…>` values, paste)
```
You are working in the git repository at <REPO_PATH>. You have no prior context; the repo is the only source of truth.

Your task packet is docs/tasks/<TASK_ID>/brief.md. Your role is <implementer | designer | reviewer | scout>.

Do this in order:
1. Read AGENTS.md completely, then docs/STATUS.md and docs/PLAN.md.
2. Read the brief and EVERY file it links (spec, design, contract, research, existing code it says to reuse).
3. Follow docs/playbooks/task-run.md. Touch ONLY the files the brief allows. Follow docs/STANDARDS.md
   (≤200 lines per file, ≤3-line comments, names that say what the code does, reuse before writing new code).
4. Run the brief's verify command and scripts/check-standards. Fix until both pass.
5. Write docs/tasks/<TASK_ID>/report.md using docs/templates/report.md, with the FULL verify output pasted.
6. Update the task's row in docs/PLAN.md (status: NEEDS REVIEW), add a line to docs/STATUS.md with a path and verify
   command, and append one line to docs/WORKLOG.md that names your model and tool.
7. Commit with a plain message "<TASK_ID>: <one-line summary>". Include .agent-logs/. No Co-Authored-By or other trailers.

Rules: if something is unclear, contradictory or blocked, STOP and write it in the report instead of guessing.
Never change files outside the brief, never edit old .agent-logs entries, never commit secrets.
Final reply: result (DONE / PARTIAL / BLOCKED), files changed, open issues.
```

## How to launch it (prompts and responses must end up in `.agent-logs/`)
| Tool | Launch | Capture |
|---|---|---|
| Claude Code (any Claude model) | `claude --model <model>` in the repo root, paste the kickoff prompt | automatic (project hooks) |
| Codex CLI | `scripts/agent-run codex <TASK_ID>` | automatic (wrapper) |
| Gemini CLI | `scripts/agent-run gemini <TASK_ID>` | automatic (wrapper) |
| Aider + any OpenRouter model | `scripts/agent-run aider <TASK_ID>` (set the model in aider's config) | automatic (wrapper) |
| Text-only model (review, planning) | `OPENROUTER_API_KEY=… scripts/agent-run openrouter:<model-id> <TASK_ID>` | automatic (wrapper); it can't edit files, so it's only for reviewer/designer text output |
| Cursor / IDE chat / web UI | paste the kickoff prompt | **manual:** export the chat into `.agent-logs/<date>_<tool>_<TASK_ID>.md` before committing |

`scripts/agent-run` sends the brief itself as the prompt. Every brief starts with the same "read AGENTS.md first" instructions, so the kickoff prompt is only needed for tools that you paste into by hand.

## Writing a new brief (orchestrator)
1. `mkdir -p docs/tasks/<TASK_ID>` and copy `docs/templates/delegation-brief.md` → `brief.md`.
2. Fill in every section. **Allowed files** and **Verify command** must never be empty.
3. Add the task row to `docs/PLAN.md` with the status `READY FOR HANDOFF`.
4. Commit the brief **before** handing it off, so the agent starts from a clean tree.

## After the agent finishes (reviewer, on a different model)
1. Re-run the verify command yourself. Never trust the pasted output alone.
2. Check the diff against the spec's acceptance criteria and `docs/STANDARDS.md`.
3. Pass: set the PLAN status to DONE and tick `tasks.md`. Fail: write the issues into a new brief `<TASK_ID>-fix`.
