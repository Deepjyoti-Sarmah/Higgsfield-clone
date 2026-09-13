# Tasks NNN: <feature name>

Rules:
- One task = one agent run.
- File sets don't overlap between tasks that run in parallel.
- Every task has a verify command.

- [ ] **T-NNN-1** · <title>
  - Files: `apps/api/...`
  - Verify: `cd apps/api && pytest tests/test_x.py -q`
  - Suggested role: implementer · Depends on: —
- [ ] **T-NNN-2** · <title>
  - Files:
  - Verify:
  - Suggested role: · Depends on: T-NNN-1
