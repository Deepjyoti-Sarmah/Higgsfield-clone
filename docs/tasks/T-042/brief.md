# Brief T-042: `scripts/task`, a harness-agnostic task protocol (claim, talk, verify, submit, review)

**Role:** implementer (small/medium model, any harness) · **Tooling only: no app code, no API, no web changes**

You are the implementer for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md` (the size and naming rules are enforced by `scripts/check-standards`).
2. Read `scripts/agent-run` and `scripts/check-standards`. Match their style: Python 3 standard library only, short functions, no docstrings that repeat the name, comments of 3 lines at most that explain *why*.
3. Read this brief to the end before writing anything.

## Why this exists
From now on, task packets will be implemented by agents running in **different harnesses** (Codex, opencode, Crush, Claude Code, IDE chats, and others not known yet). They share no chat context. The only shared memory is the git repo. We need one small CLI that any harness able to run a shell command can use to:
- see which tasks are free
- claim one without colliding with another agent
- work in isolation
- ask questions and get answers
- run the exact same verification the orchestrator will re-run
- submit with its transcript captured
- receive a review

This tool bootstraps itself. **T-042 is done the old way** (see "Report" at the bottom), not through the tool it builds.

## Goal
An executable `scripts/task` with subcommands `list`, `show`, `claim`, `say`, `verify`, `submit`, `review`, `release` and `board`, backed by a small `scripts/tasklib/` package and covered by pytest tests that run against a throwaway git repo.

## Allowed files (touch nothing else)
- `scripts/task` (new, executable, `#!/usr/bin/env python3`)
- `scripts/tasklib/__init__.py` (new, empty)
- `scripts/tasklib/*.py` (new; suggested split below)
- `scripts/tests/test_task_*.py` (new; one or more files)
- `scripts/tests/conftest.py` (new, if you need shared fixtures)
- `.gitignore` (add exactly one line: `.worktrees/`)
- `docs/tasks/T-042/report.md` (new)

If you believe another file must change, **stop** and say so in `report.md`. Do not edit `AGENTS.md`, playbooks or templates; T-043 does that.

## Must reuse
- `.claude/hooks/capture.py`: import `log_path` and `write_entry` exactly the way `scripts/agent-run` does (`sys.path.insert(0, str(ROOT / ".claude" / "hooks"))`). Use them for the transcript copy in `submit`, so the logs share one format.
- `scripts/check-standards`: `verify` runs it as a subprocess. Do not re-implement it.

## Concepts (read carefully; the tests depend on these exact formats)

### Main checkout vs worktree
- **Main checkout:** the first path printed by `git worktree list --porcelain` (the line `worktree <path>`). The board lives here: every task's `status` and `thread.md`, and `docs/tasks/BOARD.md`. Board changes are always committed **on the main checkout's current branch** (`main`).
- **Task worktree:** `<main>/.worktrees/<TASK>` on branch `task/<TASK>`. Implementers write code there. `verify` and `submit` operate on the worktree the command is run from (`git rev-parse --show-toplevel` of the current directory).

### Packet directory: `docs/tasks/<TASK>/`
| File | Written by | Lives on |
|---|---|---|
| `brief.md` | orchestrator | main (already there before claim) |
| `status` | `scripts/task` only | main |
| `thread.md` | `scripts/task say` / `review` only | main |
| `verify.log` | `scripts/task verify` | the task branch |
| `report.md` | implementer | the task branch |

A task is **on the board** only when both `brief.md` and `status` exist. `<TASK>` is the directory name, for example `T-042` or `T-044-1`.

### `status` file format: exactly one line
```
open
claimed <owner> <utc>
blocked <owner> <utc>
submitted <owner> <utc>
changes-requested <owner> <utc>
accepted <owner> <utc>
```
- `<owner>` is `<agent>@<harness>`, for example `deepseek-v3@opencode` or `gpt-5-mini@codex`. It contains no spaces.
- `<utc>` is `YYYY-MM-DDTHH:MM:SSZ`, the time of the last transition.
- `owner` is set by `claim` and kept by every later transition except `release`, which writes a bare `open`.

### Transitions: the only allowed moves (keep this table in ONE place in code)
| Action | Allowed from | To |
|---|---|---|
| claim | open | claimed |
| block (a QUESTION was asked) | claimed, changes-requested | blocked |
| unblock (an ANSWER was given) | blocked | claimed |
| submit | claimed, changes-requested | submitted |
| accept | submitted | accepted |
| request-changes | submitted | changes-requested |
| release | anything except accepted | open |

Any other move exits non-zero with `error: cannot <action> <TASK>: it is '<state>'`.

### `thread.md` format: append-only
Created on first write with this header:
```
# Thread <TASK>

Append-only. Write with `scripts/task say`.
```
Each entry is appended as:
```

### <utc> · <author> · <KIND>

<message>
```
`KIND` is one of `QUESTION`, `ANSWER`, `NOTE`, `REVIEW`. Never rewrite or reorder earlier entries.

### `BOARD.md`: generated, never hand-edited
`docs/tasks/BOARD.md` is rewritten on every board change. Its layout:
```
# Task board (generated by `scripts/task board`; do not edit by hand)

Generated <utc>. States: open → claimed ⇄ blocked → submitted → accepted | changes-requested.

| Task | Title | State | Owner | Since (UTC) |
|---|---|---|---|---|
| T-042 | <title> | claimed | x@y | 2026-09-25T13:00:00Z |
```
- Rows are sorted by task directory name. Tasks without a `status` file are left out.
- The title is the part after the first `:` on the first line of `brief.md`. With no `:`, use the line minus its leading `# `.
- An open task shows `-` for Owner and Since.

### Identity
Every write command takes `--as <agent>@<harness>`, or reads the env var `TASK_AS` when `--as` is missing. Reject a value without exactly one `@`, or one containing whitespace.

## Commands (exact behaviour)
All commands print `error: <message>` to stderr and exit 1 on failure, and never print a Python traceback for expected errors. Use one exception class, such as `TaskError`, caught in `main()`.

1. **`scripts/task list`**
   Prints the board rows to stdout, one per line, as `<TASK>  <state>  <owner>  <title>`. It reads from the main checkout even when run inside a worktree.

2. **`scripts/task show <TASK>`**
   Prints the brief path, the status line and the full `thread.md` (or `(no thread yet)`), all read from the **main** checkout. Implementers inside a worktree use this to see answers, because their branch copy of `thread.md` is stale.

3. **`scripts/task claim <TASK> --as A@H`**
   1. Take the board lock (see "Concurrency").
   2. Check that the task is on the board and `open`, apply `claim`, and regenerate `BOARD.md`.
   3. Commit `status` and `BOARD.md` on main with the message `<TASK>: claimed by A@H`.
   4. Create the worktree:
      - If branch `task/<TASK>` does not exist: `git worktree add -b task/<TASK> .worktrees/<TASK> HEAD`, run from main *after* the claim commit.
      - If it exists: `git worktree add .worktrees/<TASK> task/<TASK>`.
      - If the worktree directory already exists, reuse it.
   5. For each of `apps/web/node_modules` and `apps/api/.venv`: if it exists in main and is missing in the worktree, create a **symlink** to the main copy, so verify commands work without a reinstall.
   6. Print the worktree path and the next steps (`cd <path>`, read the brief, `scripts/task verify`, `scripts/task submit`).

4. **`scripts/task say <TASK> <KIND> <message...> --as A@H`**
   1. Append a thread entry on main.
   2. If KIND is `QUESTION`, also apply `block`. If KIND is `ANSWER` and the task is `blocked`, apply `unblock`.
   3. Regenerate `BOARD.md` and commit the changed files on main: `<TASK>: <KIND> from A@H`.
   The message is all remaining positional words joined with spaces. `-` means read the message from stdin, for long multi-line text.

5. **`scripts/task verify <TASK>`** (run from inside a worktree, or from main for the orchestrator's re-run)
   1. Read `docs/tasks/<TASK>/brief.md` **from the current worktree**. Take the first fenced code block after the heading line that starts with `## Verify command`. If there isn't one, raise an error.
   2. Run it with `bash -o pipefail -c "<block>"`, cwd set to the current worktree root, capturing stdout and stderr together.
   3. Then run `scripts/check-standards` in the same root.
   4. Write `docs/tasks/<TASK>/verify.log` in the current worktree:
      ```
      # verify <TASK>
      when: <utc>
      root: <worktree path>
      head: <git rev-parse HEAD>
      fingerprint: <tree hash, see below>

      ## command
      <the block>

      ## output (exit <code>)
      <combined output>

      ## check-standards (exit <code>)
      <output>

      RESULT: PASS
      ```
      `RESULT` is `PASS` only when both exit codes are 0; otherwise `FAIL`.
   5. Print the `RESULT` line and exit 0 on PASS, 1 on FAIL.

   **Fingerprint:** the git tree hash of the worktree's current content, **excluding** `docs/tasks/<TASK>/` and `.agent-logs/`. Compute it without touching the real index:
   1. Make a temp dir and set `GIT_INDEX_FILE=<tmp>/index` in a copied env.
   2. `git read-tree HEAD`
   3. `git add -A -- . ':(exclude)docs/tasks/<TASK>' ':(exclude).agent-logs'`
   4. `git write-tree`

   It proves the code the log describes is the code being submitted, while the implementer can still write `report.md` after verifying.

6. **`scripts/task submit <TASK> --as A@H [--transcript <file>]`** (run from inside the task worktree)
   Refuse, with a clear error, when any of these is true:
   - the current root is the main checkout;
   - `report.md` is missing;
   - `verify.log` is missing or not `RESULT: PASS`;
   - the fingerprint in `verify.log` differs from the current fingerprint (the message says "code changed since verify; run scripts/task verify again");
   - `--transcript` is missing and the harness part of A@H is not `claude-code`. Claude Code captures itself through hooks.

   Otherwise:
   1. If `--transcript` is given, copy its text into `.agent-logs/` of the current worktree using `capture.log_path` and `write_entry`. Use session id `<harness>_<TASK>`, kind `RESPONSE`, with model = the agent part and tool = the harness part.
   2. In the worktree: `git add -A`, then commit on the task branch with `<TASK>: submit by A@H`. Skip the commit if nothing is staged.
   3. On main: apply `submit`, append a `NOTE` saying `submitted at <branch head sha>`, regenerate `BOARD.md`, and commit `<TASK>: submitted by A@H`.

7. **`scripts/task review <TASK> accept|changes <message...> --as A@H`** (orchestrator or reviewer)
   Append a `REVIEW` entry whose first line is `ACCEPTED` or `CHANGES REQUESTED`, followed by the message. Apply `accept` or `request-changes`, regenerate the board, and commit on main. It does **not** merge. Merging stays a deliberate human or orchestrator step.

8. **`scripts/task release <TASK> <reason...> --as A@H`**
   Append a `NOTE` with the reason, apply `release`, regenerate the board and commit. Leave the branch and worktree in place.

9. **`scripts/task board`**
   Regenerate `BOARD.md` and commit it only if it changed: `board: regenerate`.

### Concurrency
Every command that writes to the board holds an exclusive `fcntl.flock` on `<git common dir>/task-board.lock` (find it with `git rev-parse --git-common-dir`, resolved against main) from reading the status until the commit is done. Two agents claiming the same task at once: exactly one wins, and the other gets the "cannot claim … it is 'claimed'" error.

### Committing on main without sweeping other work
1. `git add -- <paths>`
2. `git commit --quiet -m "<msg>" -- <paths>`

A pathspec commit records only those files, so anything else the orchestrator has staged on main stays out of it. Never run `git add -A` on main.

## Suggested module split (each file ≤ 200 lines, functions ≤ ~40 lines)
- `tasklib/paths.py`: `TaskError`, `run_git`, `find_main_root`, `find_current_root`, `task_dir`, `worktree_path`, `branch_name`, `utc_now`, and `DEPENDENCY_DIRS` with a one-line *why* comment.
- `tasklib/state.py`: the `STATES` tuple, the transitions table, a `Status` dataclass, `parse_status`, `read_status`, `apply_transition`, `board_lock`, `commit_on_main`.
- `tasklib/board.py`: `read_title`, `list_board_rows`, `render_board`, `write_board`, `append_thread_entry`.
- `tasklib/worktree.py`: `create_task_worktree`, `link_dependencies`.
- `tasklib/verify.py`: `extract_verify_command`, `compute_fingerprint`, `run_verify`, `read_verify_result`.
- `tasklib/submit.py`: `copy_transcript`, `submit_task`.
- `scripts/task`: argparse subcommands, a `parse_identity` helper, dispatch, and the `TaskError` → exit 1 handler.

Names follow STANDARDS: verb + noun. The banned names (`utils`, `helpers`, `manager`, `data`, `handle`, `process`, `misc`, `common`) apply to modules, functions and variables.

## Tests (pytest; required)
Put them in `scripts/tests/`. Each test builds a **throwaway repo in `tmp_path`**:
1. `git init -b main`, set a local user.name and user.email, and copy in `scripts/` (so `scripts/check-standards` exists) and `.claude/hooks/capture.py`.
2. Add a `docs/tasks/T-900/brief.md` with a title line and a `## Verify command` block of `true`, plus a `status` of `open`. Commit.
3. Run `scripts/task` as a subprocess with `cwd` set to that repo (or a worktree inside it).

Cover at least:
- [ ] `list` shows `T-900  open`
- [ ] `claim` writes `claimed x@y <utc>`, commits on main, and creates `.worktrees/T-900` on branch `task/T-900`
- [ ] a second `claim` fails with the "cannot claim" error and exit 1
- [ ] `say … QUESTION` makes the state `blocked` and appends a correctly formatted thread entry; `say … ANSWER` returns it to `claimed`
- [ ] `verify` with a passing block writes `verify.log` ending in `RESULT: PASS` with a fingerprint line; with a block of `false` it ends in `RESULT: FAIL` and exits 1
- [ ] `submit` without `report.md` is refused; with a stale fingerprint (a file changed after verify) it is refused; without `--transcript` for a non-`claude-code` harness it is refused
- [ ] a successful `submit` commits on `task/T-900`, copies the transcript into `.agent-logs/`, and sets main's status to `submitted`
- [ ] `review … changes` → `changes-requested`, then `submit` again works; `review … accept` → `accepted`; `release` on an accepted task fails
- [ ] `BOARD.md` has the header and one row per task on the board
- [ ] `--as` without `@` is rejected; `TASK_AS` works when `--as` is missing
- [ ] a pathspec commit on main leaves an unrelated staged file staged and uncommitted

Keep each test file ≤ 200 lines. Split into `test_task_board.py`, `test_task_verify.py`, `test_task_submit.py` and so on, with a shared fixture in `conftest.py`.

## Acceptance checks
- [ ] Every command above behaves exactly as specified, including the error messages quoted
- [ ] The file formats (`status`, `thread.md`, `verify.log`, `BOARD.md`) match the examples byte for byte in structure
- [ ] No third-party dependencies; Python 3.11+ standard library only (plus pytest for tests)
- [ ] `.gitignore` contains `.worktrees/`
- [ ] No expected error prints a traceback
- [ ] All tests pass and `scripts/check-standards` passes

## Verify command (paste its full output in report.md)
```
chmod +x scripts/task && apps/api/.venv/bin/python -m pytest scripts/tests -q && scripts/task list && scripts/check-standards
```

## Out of scope
- Editing `AGENTS.md`, playbooks, templates or `docs/PLAN.md` (T-043)
- Automatic merging, GitHub PRs, or any network call
- Creating new task packets: the orchestrator writes `brief.md` and `status` by hand

## Report
- Write `docs/tasks/T-042/report.md` using `docs/templates/report.md`, with the full verify output pasted.
- Capture your transcript:
  - If your harness is not Claude Code and can be wrapped, run through `scripts/agent-run <tool> T-042`.
  - Otherwise export the transcript into `.agent-logs/<utc>_<harness>_T-042.md`.
- Do **not** commit. The orchestrator re-runs the verify command, reviews, and commits.
