# Playbook: handoff (run at the end of EVERY session, any tool)

**Goal:** the next agent, on any model with no chat history, can continue from the files alone.

1. **`docs/STATUS.md`:** every line reflects reality right now. Move fixed items to WORKS and add anything you broke or found.
2. **`docs/PLAN.md`:**
   - Update the task statuses.
   - Put the **next 3 tasks** at the top of the task board, in order.
   - List blockers, with who or what unblocks them.
3. **`docs/WORKLOG.md`:** add one line per task touched.
4. **`docs/DECISIONS.md`:** add any decision made this session that isn't recorded yet.
5. **Uncommitted work:** either commit it or note in STATUS exactly what's half-done and where.
6. **Commit, including `.agent-logs/`.** Plain message, no attribution trailers.
