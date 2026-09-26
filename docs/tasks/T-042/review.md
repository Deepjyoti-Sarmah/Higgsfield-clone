# Review T-042

**Reviewer:** claude-sonnet-5 @ claude-code (implementer was muse-spark @ opencode; follow-up commits e629dc1 and 6903533 are the orchestrator's).
**Verdict: ACCEPT** (no blockers or majors; two minors).

## Verify (re-run)
`apps/api/.venv/bin/python -m pytest scripts/tests -q && scripts/task list && scripts/check-standards`: 19 passed (18 reported plus the test added in e629dc1), the board listed, `check-standards: ok (0 violations)`.

## Acceptance checks
- [x] yes: every command behaves as specified. Nine subcommands in `scripts/task:91-121`; quoted errors seen live: `cannot claim T-900: it is 'claimed'`, `code changed since verify; run scripts/task verify again`, `invalid identity 'bad': use <agent>@<harness>`, `task T-999 is not on the board`.
- [x] yes: formats match the brief. `status` one line (`scripts/tasklib/state.py:51-67`); thread entries and `BOARD.md` header (`scripts/tasklib/board.py:41-70`); `verify.log` layout ending in `RESULT:` (`scripts/tasklib/verify.py:92-112`).
- [x] yes: stdlib only (Python 3, pytest in tests).
- [x] yes: `.gitignore:22` has `.worktrees/`.
- [ ] partly: one expected error prints a traceback, see F1.
- [x] yes: tests and `check-standards` pass.

## Specific checks (run in a throwaway repo under the scratchpad dir)
- **Transition table in one place:** yes, `MOVES` at `scripts/tasklib/state.py:14-25`; every move goes through `apply_transition` (`:51`). Release from `accepted` is refused, and `open` -> `open` is allowed as the table says.
- **Pathspec commits do not sweep staged files:** yes. An unrelated file staged on main stayed `A  unrelated.txt` after `say` and after `claim`; the commit contained only `thread.md` (`state.py:84-87`).
- **Fingerprint excludes the packet and `.agent-logs`:** yes. `compute_fingerprint` (`verify.py:40-68`) also `git rm --cached` the paths; the implementer's deviation is justified (the brief's recipe alone fails on resubmit) and documented in `report.md`.
- **Submit refuses a stale fingerprint:** yes (`submit.py:35`). Live: changed a file after verify, submit refused twice; after reverting the change it succeeded and committed on `task/T-901` (`252309e`), main status became `submitted`.
- **Refusals in order:** main checkout (`submit.py:28`), missing `report.md` (`:30`), no passing `verify.log` (`:33`), stale fingerprint (`:35`), missing `--transcript` for a non-`claude-code` harness (`:37`).
- **Concurrent claim:** two simultaneous `claim T-900` processes: exactly one won, the other got the `cannot claim ... 'claimed'` error, one claim commit. Not covered by the test suite (the report says so).
- **STANDARDS:** every file <= 132 lines; no banned names found by grep; comments are <= 3 lines.

## Follow-up commits
- **e629dc1 (COMPOSE_PROJECT_NAME): accept.** `build_verify_env` (`verify.py:71-77`) defaults the compose project to the main checkout's folder name, sanitised the way compose does (lowercase, `[a-z0-9_-]`). `setdefault` lets an explicit env value win, the fingerprint is unaffected, and it has a test. Only caveat: a main folder starting with `-` or `_` would produce a name compose rejects; not realistic here.
- **6903533 (.gitignore): accept.** `.venv` and `node_modules` without a trailing slash also match the symlinks that `link_dependencies` creates in worktrees, which the old directory-only patterns missed (submit's `git add -A` committed the symlink). It was outside the brief's "one line" limit but it fixes a real defect found in use.

## Findings
- **F1 (minor)** `scripts/task verify <unknown task>` prints a `FileNotFoundError` traceback: `extract_verify_command` reads `brief.md` without checking it exists (`scripts/tasklib/verify.py:14`). Expected error, so it breaks "no traceback"; fix by raising `TaskError(f"task {task} is not on the board")`. Add a test.
- **F2 (minor)** `scripts/task say <TASK> FOO ...` with a bad KIND is rejected by argparse (`choices`) with usage text and exit 2, not `error: ...` exit 1. Harmless; mention only for consistency.
- **F3 (nit)** No two-process claim race test; the lock works (checked by hand) but is not guarded by the suite.
