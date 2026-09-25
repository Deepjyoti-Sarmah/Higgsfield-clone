#!/usr/bin/env python3
import sys
from pathlib import Path

from tasklib.board import append_thread_entry, write_board
from tasklib.paths import TaskError, find_current_root, find_main_root, run_git, task_dir, utc_now
from tasklib.state import apply_transition, board_lock, commit_on_main
from tasklib.verify import compute_fingerprint, read_verify_result


def copy_transcript(work_root, task, transcript, agent, harness):
    # Reuse the capture format so all transcripts read the same.
    sys.path.insert(0, str(work_root / ".claude" / "hooks"))
    from capture import log_path, write_entry

    body = Path(transcript).read_text(encoding="utf-8")
    session = f"{harness}_{task}"
    logs = work_root / ".agent-logs"
    logs.mkdir(parents=True, exist_ok=True)
    path = log_path(str(logs), session)
    write_entry(path, session, "RESPONSE", body, agent, tool=harness)


def submit_task(task, identity, transcript):
    agent, _, harness = identity.partition("@")
    work_root = find_current_root(Path.cwd())
    main_root = find_main_root(Path.cwd())
    if work_root == main_root:
        raise TaskError("submit must run inside the task worktree, not the main checkout")
    if not (task_dir(work_root, task) / "report.md").exists():
        raise TaskError(f"task {task} has no report.md; write it before submitting")
    ok, logged_tree = read_verify_result(work_root, task)
    if not ok:
        raise TaskError(f"task {task} has no passing verify.log; run scripts/task verify again")
    if compute_fingerprint(work_root, task) != logged_tree:
        raise TaskError("code changed since verify; run scripts/task verify again")
    if transcript is None and harness != "claude-code":
        raise TaskError(f"--transcript is required for harness '{harness}'")
    if transcript is not None:
        copy_transcript(work_root, task, transcript, agent, harness)
    run_git(["add", "-A"], cwd=work_root)
    if run_git(["status", "--porcelain"], cwd=work_root):
        run_git(["commit", "--quiet", "-m", f"{task}: submit by {identity}"], cwd=work_root)
    head = run_git(["rev-parse", "HEAD"], cwd=work_root)
    with board_lock(main_root):
        apply_transition(task_dir(main_root, task), task, "submit", identity)
        append_thread_entry(main_root, task, utc_now(), identity, "NOTE", f"submitted at {head}")
        write_board(main_root)
        commit_on_main(
            main_root,
            [
                f"docs/tasks/{task}/status",
                f"docs/tasks/{task}/thread.md",
                "docs/tasks/BOARD.md",
            ],
            f"{task}: submitted by {identity}",
        )
    return head
