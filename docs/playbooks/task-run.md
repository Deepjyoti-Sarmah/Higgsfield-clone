# Playbook: task-run

**Input:** `docs/tasks/T-NNN-k/brief.md`.
**Output:** worktree changes + `report.md`, submitted for review.
**Role:** implementer (then a reviewer on a different model)

1. **Claim:** `scripts/task claim <TASK> --as <agent>@<harness>`, then `cd` into the worktree it prints.
2. **Load context:** `AGENTS.md` → brief → linked spec/design → `docs/STANDARDS.md`. Read `STATUS.md` for anything broken nearby.
3. **Search before writing:** look for existing pieces in `ui/`, `services/`, `repositories/` and `adapters/`. Reuse them.
4. **Implement** in the worktree, within the allowed files only. Keep every file ≤200 lines.
5. **Run `scripts/task verify <TASK>`** (runs the verify block and `check-standards`, writes `verify.log`). Fix until it passes, or stop and report BLOCKED.
6. **Write `report.md`** (template `docs/templates/report.md`), then **`scripts/task submit <TASK>`** with the transcript captured. Never commit on `main` yourself.
7. **Orchestrator:** re-runs verify itself, has a **different model** review the diff, then merges with `git merge --no-ff task/<TASK>` and does the definition-of-done updates in that merge (STATUS, WORKLOG, `tasks.md` tick, `.agent-logs/`). Details: `docs/playbooks/multi-harness.md`.
