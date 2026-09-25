# Brief T-043: Switch the docs and templates to the `scripts/task` protocol

**Role:** implementer (small/medium model, any harness) · **Docs only: no code**
**Depends on T-042** (`scripts/task` exists and is merged). This is the **first task done through the new protocol**, so use it for real:
- claim it with `scripts/task claim`
- ask any questions with `scripts/task say`
- finish with `scripts/task verify` and `scripts/task submit`

You are the implementer for this one task. Your first steps:
1. Read `AGENTS.md`, then run `scripts/task show T-043`.
2. Read `docs/tasks/T-042/brief.md` completely. It is the specification of the protocol you are documenting. The "Commands" and "Concepts" sections are the source of truth; do not invent behaviour that isn't there.
3. Read every file under "Allowed files" below before editing it.

## Why
Agents in unknown harnesses will pick up tasks with no chat context. Today the docs describe the old flow: hand the agent a brief, the agent commits to `main` itself and hand-edits the PLAN rows. Every entry point an agent might read has to describe the new flow the same way:
- claim
- work in the worktree
- `say` for questions
- `verify`
- `submit`
- the orchestrator reviews and merges

## Allowed files (touch nothing else)
- `AGENTS.md`
- `docs/playbooks/task-run.md`
- `docs/playbooks/multi-harness.md` (new)
- `docs/templates/delegation-brief.md`
- `docs/templates/report.md`
- `docs/templates/handoff-prompt.md`
- `docs/templates/handoff-prompt-small.md`
- `docs/PLAN.md` (only the "Task board" heading area; see step 7)
- `docs/tasks/T-043/report.md` (new)

## The changes

1. **`docs/playbooks/multi-harness.md` (new, ≤ 120 lines).** The full protocol for any agent, in this order:
   - A one-paragraph "why": the repo is the only shared memory, and harnesses differ.
   - The lifecycle as a small table: `open → claimed ⇄ blocked → submitted → accepted | changes-requested`, and who moves each step.
   - **Implementer steps**, as a numbered list of copy-pasteable commands:
     1. `scripts/task list`
     2. `scripts/task claim <TASK> --as <agent>@<harness>` (or `export TASK_AS=…`)
     3. `cd .worktrees/<TASK>`
     4. read the brief
     5. work
     6. `scripts/task say <TASK> QUESTION "…"` when blocked, then `scripts/task show <TASK>` to read the answer
     7. `scripts/task verify <TASK>`
     8. write `report.md`
     9. `scripts/task submit <TASK> --transcript <file>`
   - **Orchestrator/reviewer steps:**
     1. `scripts/task show`
     2. answer with `say … ANSWER`
     3. `cd .worktrees/<TASK> && scripts/task verify <TASK>` (the re-run)
     4. `git diff main...task/<TASK>`
     5. `scripts/task review <TASK> accept|changes "…"`
     6. then merge on main with `git merge --no-ff task/<TASK>` and do the definition-of-done updates in that merge (STATUS, WORKLOG, `tasks.md` tick)
   - **Transcript capture per harness:** Claude Code is captured by hooks (`--as <model>@claude-code`, no `--transcript`); `scripts/agent-run` for Codex, Gemini, Aider and opencode; everything else exports the chat to a file and passes `--transcript`.
   - **Identity naming:** `<model>@<harness>`, lowercase, no spaces, for example `deepseek-v3@opencode`, `gpt-5-mini@codex`, `sonnet-5@claude-code`.
   - **Rules:**
     - Never edit `status`, `thread.md` or `BOARD.md` by hand.
     - Never commit on `main` yourself.
     - Never merge your own branch.
     - The reviewer must be a different model from the implementer.
   - **Known limits:** tests that use the shared dev database can race when two worktrees run pytest at once (see STATUS BROKEN). Run DB-backed verifies one at a time.

2. **`AGENTS.md`:**
   - In "Read order", insert a step after STATUS: "`docs/tasks/BOARD.md` + `scripts/task list`: which tasks are open".
   - Replace the **Definition of done** checklist with two short lists:
     - **Implementer:** `scripts/task verify` passes; `report.md` is written; `scripts/task submit` is done, with the transcript captured.
     - **Orchestrator, at merge:** re-ran verify, reviewed by a different model, `review accept`, merged with `--no-ff`, ticked `tasks.md`, updated STATUS and WORKLOG, included `.agent-logs/`, plain commit message with no trailers.
   - In "The task packet is the whole interface", list the packet files: `brief.md`, `status`, `thread.md`, `verify.log`, `report.md`.
   - Add a row to the Playbooks table: `docs/playbooks/multi-harness.md` | "claiming, doing and submitting a task from any harness".
   - Keep AGENTS.md's structure and every other section as it is. Keep the file under 120 lines.

3. **`docs/playbooks/task-run.md`:** rewrite it into the new flow. Steps 1–5 become: claim, load context, search before writing, implement in the worktree, `scripts/task verify`, `report.md`, `scripts/task submit`. Step 6 (the orchestrator's re-run and review) points to `multi-harness.md`. Step 7 (the one merge commit with DoD updates) stays, now done by the orchestrator. Remove "the implementer updates PLAN/STATUS/WORKLOG and commits". Keep it ≤ 30 lines.

4. **`docs/templates/delegation-brief.md`:**
   - In "Your first steps", add a first step: "`scripts/task claim <TASK> --as <you>` and `cd` into the worktree it prints".
   - Replace the "Report" section with: write `report.md`, run `scripts/task verify` then `scripts/task submit`, and don't commit on main.
   - Keep the note that the `## Verify command` heading must contain exactly one fenced block, because `scripts/task verify` runs the first block under that heading.

5. **`docs/templates/report.md`:**
   - Change the first line to `**Agent:** <model>@<harness> · **Role:** … · **Result:** DONE | PARTIAL | BLOCKED`.
   - Replace "Verify output (full paste)" with "Verify: see `verify.log` (written by `scripts/task verify`); paste only the RESULT line and anything notable".

6. **`docs/templates/handoff-prompt.md` and `handoff-prompt-small.md`:** update both kickoff prompts so the steps are:
   1. read AGENTS.md
   2. `scripts/task claim …`
   3. work only in the worktree
   4. `scripts/task say … QUESTION` instead of guessing
   5. `scripts/task verify`
   6. write the report
   7. `scripts/task submit`

   Remove the steps that tell the agent to edit PLAN, STATUS or WORKLOG or to commit. In `handoff-prompt.md`, update the "Writing a new brief" section: the orchestrator also writes a `status` file containing `open`, runs `scripts/task board`, and commits both before handing off. Keep the launch/capture table and add a column note that `--transcript` is needed for non-wrapped harnesses.

7. **`docs/PLAN.md`:** directly under the `## Task board` heading, add one line: "From T-042 on, the live board is `docs/tasks/BOARD.md` (generated by `scripts/task`). This table is history." Change nothing else.

## Acceptance checks
- [ ] A new agent reading only AGENTS.md → `multi-harness.md` → a brief can complete a task with no other instructions
- [ ] Every command shown exists in T-042's spec with the same arguments; no invented flags
- [ ] No doc still tells an implementer to commit on main or hand-edit PLAN, STATUS or WORKLOG
- [ ] AGENTS.md ≤ 120 lines, `multi-harness.md` ≤ 120 lines, `task-run.md` ≤ 30 lines
- [ ] Plain, direct prose (run the `no-ai-slop` skill's Detect mode over the new playbook if your harness can)
- [ ] `scripts/check-links` and `scripts/check-standards` pass

## Verify command
```
scripts/check-links && scripts/check-standards && wc -l AGENTS.md docs/playbooks/multi-harness.md docs/playbooks/task-run.md
```

## Out of scope
- Any change to `scripts/task` or `tasklib`. If you find a bug in it, report it with `scripts/task say T-043 NOTE "…"` and in `report.md`.
- Specs 010+ and UI work

## Report
Write `docs/tasks/T-043/report.md` from the updated template, then run `scripts/task verify T-043` and `scripts/task submit T-043 --as <you> [--transcript <file>]`. Do not commit on main.
