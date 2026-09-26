# Rules for every spec 011 task (read before your brief)

1. **Start:** `scripts/task claim <TASK> --as <model>@<harness>`, then `cd .worktrees/<TASK>`. Work only there, and only in the brief's **Allowed files**. If you need another file, `scripts/task say <TASK> QUESTION "…"` and stop.
2. **Read:** `AGENTS.md` (Hard rules), `docs/STANDARDS.md`, `docs/specs/011-quality-faceswap-trim/spec.md`, then your brief and every file it names. For UI work also read `DESIGN.md`.
3. **Standards (enforced by `scripts/check-standards` and eslint):**
   - ≤ 200 lines per file, functions ≤ 40 lines, eslint complexity ≤ 8
   - comments of 3 lines at most, explaining *why*
   - verb + noun names; no `utils`, `helpers`, `manager`, `data`, `handle`, `process`, `misc` or `common`
   - web colours only from tokens
   - no new npm dependencies (jsdom isn't installed; test pure functions)
4. **Verify:** `scripts/task verify <TASK>` runs the brief's verify block plus `check-standards` and writes `verify.log`. It must end in `RESULT: PASS`. If it fails 3 times on the same thing, stop and report PARTIAL.
5. **Shared dev DB:** before any API verify, `docker compose up -d --wait db minio` from the main checkout. Stop any stray local `python -m app.worker` (it races the tests).
6. **Finish:**
   1. Write `docs/tasks/<TASK>/report.md` (template `docs/templates/report.md`): files changed, what you reused, the RESULT line, acceptance checks yes/no with evidence, and open issues.
   2. `scripts/task submit <TASK> --as <you>`. Claude Code needs no `--transcript`; others pass `--transcript <file>`.
7. **Never:** commit on main, push, deploy to Railway, change Railway variables, or add Co-Authored-By or any other trailer. Modal deploys are allowed **only** where a brief says so.
8. **GPU spend:** only the live test renders your brief asks for.
