# Handoff prompt for SMALL agents (Haiku, Gemini Flash, small OpenRouter / local models)

Use this for **scout** tasks, and for **implementer** tasks that are tiny, mechanical and fully specified. Examples:
- 1–3 files, fewer than ~80 changed lines
- the exact change already described
- no design decisions left to make

Small agents must not: design, pick libraries, change contracts, edit more than the listed files, or commit.
If a task needs judgement, give it to a strong model with `docs/templates/handoff-prompt.md` instead.

## Rules for the brief a small agent gets
- **Allowed files:** list at most 3 exact paths (no globs).
- **The change:** describe it concretely, as "replace X with Y in function Z", and include a code snippet when it's short.
- **Verify command:** a single copy-pasteable command. Also state what "pass" looks like.
- **Stop conditions:** say when to stop and report instead of improvising.

## Kickoff prompt (copy, replace `<…>`, paste)
```
You are a careful junior engineer doing ONE small task in the git repository at <REPO_PATH>.
Your task file is docs/tasks/<TASK_ID>/brief.md. Follow it exactly. Do not do anything it does not ask for.

STEP 1: Read these files, in this order, and nothing else unless the brief links it:
  a. AGENTS.md (only the "Hard rules" section is required)
  b. docs/tasks/<TASK_ID>/brief.md
  c. every file listed under "Allowed files" in the brief

STEP 2: Before editing, write down (in your reply) the exact files you will change and a one-line plan per file.
  If the brief's plan is unclear, or it needs a file that is not in "Allowed files", STOP and go to STEP 6 with status BLOCKED.

STEP 3: Make the change. Keep everything else in each file exactly as it was. Do not rename, reformat,
  or "improve" code the brief did not mention. Keep each file at 200 lines or fewer, and comments at 3 lines or fewer.

STEP 4: Run the verify command from the brief exactly as written. Then run: scripts/check-standards
  If a command fails: read the error, fix only what the error points to, and run it again.
  If it still fails after 2 fix attempts, STOP and go to STEP 6 with status PARTIAL.

STEP 5: Check each box under "Acceptance checks" in the brief, one by one. For each, say yes/no and why in one line.

STEP 6: Write docs/tasks/<TASK_ID>/report.md with exactly these sections:
  ## Status        DONE | PARTIAL | BLOCKED
  ## Model/tool    your model name and the tool you run in
  ## Files changed one line per file
  ## Verify output the full terminal output of STEP 4 (paste it, do not summarise)
  ## Checks        the list from STEP 5
  ## Problems      anything unclear, failing or skipped (write "none" if none)

Do NOT commit, push, install new packages, or edit docs/PLAN.md, docs/STATUS.md or docs/WORKLOG.md.
A reviewer on a bigger model re-runs your verify command and commits.
Final reply: the Status line and the list of files changed.
```

## Launch and capture
- **Claude Code:** `claude --model haiku` in the repo root, then paste the kickoff prompt. Captured automatically.
- **Other CLIs or OpenRouter:** `scripts/agent-run <tool> <TASK_ID>`, as in `docs/templates/handoff-prompt.md`. The wrapper sends only the brief, so paste the kickoff steps at the top of the brief when using it this way.

## After it finishes (reviewer, bigger model)
1. `git diff`: confirm only the allowed files changed.
2. Re-run the verify command yourself.
3. If it's good, update PLAN/STATUS/WORKLOG and commit with a plain message (`<TASK_ID>: …`), including `.agent-logs/`.
4. If it isn't, write `docs/tasks/<TASK_ID>-fix/brief.md`, or do the fix yourself.
