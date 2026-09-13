# Playbook: spec-new

**Input:** a product-map row marked P0/P1.
**Output:** `docs/specs/NNN-slug/{spec,design,tasks}.md` + a row in PLAN.md.
**Role:** orchestrator

1. Pick the next free NNN. `mkdir docs/specs/NNN-slug` and copy the three templates from `docs/templates/`.
2. **spec.md:** write the story, testable acceptance criteria, all four UI states and out of scope. Link the flow doc and its screenshots.
3. **Stop and get user approval of the spec** (the only human gate). Set Status: APPROVED.
4. **design.md:**
   - API contract first, then data, flow, the file list with responsibilities, and what gets reused.
   - Check it against `docs/architecture/architecture.md` invariants and `docs/STANDARDS.md`.
5. **tasks.md:**
   - Split the work so each task is one agent run with a disjoint file set and a verify command.
   - The first task is always "routes + schemas + regenerate openapi.json".
6. For each task to delegate, write `docs/tasks/T-NNN-k/brief.md` from `delegation-brief.md`.
7. Add the tasks to the board in `docs/PLAN.md`. Commit.
