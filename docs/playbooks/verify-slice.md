# Playbook: verify-slice

**Input:** a spec whose tasks are all ticked.
**Output:** `docs/verification/NNN-slug/` screenshots + STATUS lines.
**Role:** reviewer (any model with browser access; otherwise a human with this checklist)

1. Deploy is done and `GET /api/health` on the live URL returns ok.
2. Open the **live URL in a fresh signed-out browser** (incognito). Never test on localhost.
3. Walk through every acceptance criterion in `spec.md`, in order.
   - Screenshot each result as `docs/verification/NNN-slug/AC-n.png`.
   - Also trigger each UI state (empty, loading, error, success) where you can.
4. **Record each AC as a result:**
   - A pass becomes a WORKS row in `docs/STATUS.md` citing the screenshot.
   - A failure becomes a BROKEN row, plus a new task in `tasks.md` and in `docs/PLAN.md`.
5. Set the spec's Status to DONE only if every AC passed. Commit, including `.agent-logs/`.
