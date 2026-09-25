# Kickoff prompt for T-042 (paste into any harness)

T-042 builds the task protocol itself, so it runs the old way: no `scripts/task` yet, and the agent works on a clean `main` checkout without committing.

```
You are working in the git repository at /home/deepjyoti/Documents/Assigment/Higgsfield.
You have no prior context; the repo is the only source of truth.

Your task packet is docs/tasks/T-042/brief.md. Your role is implementer.

Do this in order:
1. Read AGENTS.md (the "Hard rules" section is required), then docs/STANDARDS.md.
2. Read docs/tasks/T-042/brief.md completely, then scripts/agent-run, scripts/check-standards
   and .claude/hooks/capture.py (you must reuse log_path and write_entry from it).
3. Before editing, list the files you will create and one line of plan per file.
   Only create or edit the files under "Allowed files" in the brief. If you need another file, STOP and say so
   in the report.
4. Build it. Python 3 standard library only. Every file ≤ 200 lines, comments ≤ 3 lines, names are verb + noun,
   no module or function called utils/helpers/manager/data/handle/process/misc/common.
5. Write the tests the brief lists, then run the brief's verify command exactly:
     chmod +x scripts/task && apps/api/.venv/bin/python -m pytest scripts/tests -q && scripts/task list && scripts/check-standards
   If it fails, fix only what the error points at and re-run. After 3 failed attempts, STOP and report PARTIAL.
6. Go through every "Acceptance checks" box in the brief and write yes/no + one line of evidence for each.
7. Write docs/tasks/T-042/report.md using docs/templates/report.md, with the FULL verify output pasted.

Rules: do NOT commit, push, install packages, or edit AGENTS.md, playbooks, templates, PLAN, STATUS or WORKLOG.
If anything in the brief is unclear or contradictory, STOP and write the question in report.md instead of guessing.
Final reply: DONE / PARTIAL / BLOCKED, the files you created, and open questions.
```

## Capture
- Codex, Gemini, Aider or opencode: `scripts/agent-run <tool> T-042` sends only the brief, so paste the block above at the top of the brief first, or launch the tool by hand and export the transcript.
- Any other harness: export the full chat to `.agent-logs/<YYYY-MM-DD_HH-MM-SS>_<harness>_T-042.md` when done.
- Claude Code: captured automatically by the project hooks.
