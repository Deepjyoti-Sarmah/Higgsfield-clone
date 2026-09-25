# Report T-042

**Agent / model / tool:** implementer · muse-spark · opencode (manual run, transcript exported to `.agent-logs/`)
**Result:** DONE

## Files changed
- `scripts/task`: argparse CLI, 9 subcommands, `parse_identity`, `TaskError` → `error:` + exit 1
- `scripts/tasklib/__init__.py`: empty package marker
- `scripts/tasklib/paths.py`: `TaskError`, `run_git`, `find_main_root`, `find_current_root`, `task_dir`, `worktree_path`, `branch_name`, `utc_now`, `DEPENDENCY_DIRS`
- `scripts/tasklib/state.py`: `STATES`, single `MOVES` table, `Status`, `parse_status`, `read_status`, `apply_transition`, `board_lock` (fcntl), `commit_on_main` (pathspec)
- `scripts/tasklib/board.py`: `read_title`, `list_board_rows`, `render_board`, `write_board`, `append_thread_entry`, `say_task`, `review_task`, `release_task`, `refresh_board`
- `scripts/tasklib/worktree.py`: `branch_exists`, `create_task_worktree`, `link_dependencies`, `claim_task`
- `scripts/tasklib/verify.py`: `extract_verify_command`, `compute_fingerprint`, `run_verify`, `read_verify_result`
- `scripts/tasklib/submit.py`: `copy_transcript` (reuses `capture.log_path`/`write_entry`), `submit_task`
- `scripts/tests/conftest.py`: throwaway-repo fixture (`git init -b main`, copies `scripts/` + `capture.py`, seeds `T-900`), `run_git`/`run_task`/`add_task` helpers
- `scripts/tests/test_task_board.py`: list, claim, double-claim, say Q/A, BOARD.md, show
- `scripts/tests/test_task_verify.py`: PASS and FAIL verify paths
- `scripts/tests/test_task_submit.py`: submit refusals, success, review cycle, release guard
- `scripts/tests/test_task_policy.py`: identity validation, `TASK_AS`, pathspec-commit isolation, board noop, release
- `.gitignore`: added one line `.worktrees/`
- `docs/tasks/T-042/report.md`: this file

## Reused
- `.claude/hooks/capture.py`: `log_path` + `write_entry` in `copy_transcript`, imported the same way as `scripts/agent-run` (`sys.path.insert`)
- `scripts/check-standards`: run as subprocess by `run_verify`, not re-implemented
- `scripts/agent-run`: matched style (stdlib only, short functions)

## Acceptance checks (yes/no + evidence)
- [x] yes — Every command behaves as specified: 18 pytest tests cover list/show/claim/say/verify/submit/review/release/board, including quoted errors (`cannot claim T-900: it is 'claimed'`, `cannot release … it is 'accepted'`, `code changed since verify; run scripts/task verify again`, `--transcript is required`, `invalid identity`)
- [x] yes — File formats match the examples: `status` asserted by regex `claimed <owner> <utc>`; `thread.md` header + `### <utc> · <author> · <KIND>` entries asserted; `BOARD.md` header + `| Task | …` row asserted; `verify.log` asserted to end in `RESULT: PASS`/`FAIL` with a `fingerprint:` line
- [x] yes — Stdlib only: imports are `argparse, contextlib, dataclasses, datetime, fcntl, os, pathlib, shutil, subprocess, sys, tempfile` (+ pytest in tests)
- [x] yes — `.gitignore` ends with `.worktrees/`
- [x] yes — No expected error prints a traceback: single `TaskError` caught in `main()`; test asserts `"Traceback" not in stderr`
- [x] yes — All tests pass and `scripts/check-standards` passes (output below)

## Verify output (full paste, no summarising)
```
chmod +x scripts/task && apps/api/.venv/bin/python -m pytest scripts/tests -q && scripts/task list && scripts/check-standards
..................                                                       [100%]
18 passed in 3.59s
T-043  open  -  Switch the docs and templates to the `scripts/task` protocol
check-standards: ok (0 violations)
```

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- Deviation (required, not optional): the brief's fingerprint recipe step 3 (`git add -A` with `:(exclude)` pathspecs) does not remove *tracked* files already loaded by `read-tree HEAD`, so after the first submit commits `verify.log`/`report.md`, every resubmit failed with "code changed since verify" — including the brief's own required test (`review changes`, then `submit` again). `compute_fingerprint` therefore appends `git rm --cached -r -q --ignore-unmatch -- docs/tasks/<TASK> .agent-logs` on the temp index (real index untouched). `--ignore-unmatch` matters: without it the whole `rm` aborts with exit 128 when `.agent-logs` is absent, removing nothing. Verified by tree diff before/after.
- `scripts/task` sets `sys.dont_write_bytecode = True` before any local import: without it, submit's `from capture import …` writes `.claude/hooks/__pycache__/` into the worktree after verify, which also poisons the next fingerprint. No `.pyc` files are created by the tool now.
- `board_lock` uses `fcntl.flock`, so `scripts/task` is Linux/macOS-only. No concurrent-claim race test (two processes racing `claim`) — lock logic follows the brief but is only exercised single-process in tests.
- Nothing skipped; no other file needed changing. No commit made (orchestrator merges).

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| `scripts/task` protocol CLI (T-042 DONE) | `scripts/task`, `scripts/tasklib/`, `scripts/tests/` | `chmod +x scripts/task && apps/api/.venv/bin/python -m pytest scripts/tests -q && scripts/task list && scripts/check-standards` (18 passed, ok) | 2026-09-25 |
