# Playbook: task-run

**Input:** `docs/tasks/T-NNN-k/brief.md`.
**Output:** code changes + `report.md` + updated state files, all in one commit.
**Role:** implementer (then a reviewer on a different model)

1. **Load context:** `AGENTS.md` → brief → linked spec/design → `docs/STANDARDS.md`. Read `STATUS.md` for anything broken nearby.
2. **Search before writing:** look for existing pieces in `ui/`, `services/`, `repositories/` and `adapters/`. Reuse them.
3. **Implement** within the allowed files only. Keep every file ≤200 lines.
4. **Run the verify command** and `scripts/check-standards`. Fix until both pass, or stop and report BLOCKED.
5. **Write `report.md`** (template `docs/templates/report.md`) with the full verify output pasted.
6. **Orchestrator:**
   - Re-run the verify command itself.
   - Have a **different model** review the diff against the acceptance criteria + STANDARDS.
7. **When accepted, in one commit:**
   - tick `tasks.md`
   - update the row in `docs/PLAN.md`
   - add a `docs/STATUS.md` line (path + verify cmd + time)
   - append to `docs/WORKLOG.md`
   - include `.agent-logs/`
   - **Commit message: plain subject + body, no Co-Authored-By or attribution trailers.**
8. If the agent wasn't Claude Code, make sure its run went through `scripts/agent-run`. No log file for the task id means not done.
