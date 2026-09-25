#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

from tasklib.board import write_board
from tasklib.paths import (
    DEPENDENCY_DIRS,
    TaskError,
    branch_name,
    find_main_root,
    run_git,
    task_dir,
    worktree_path,
)
from tasklib.state import apply_transition, board_lock, commit_on_main


def branch_exists(main_root, task):
    finished = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name(task)}"],
        cwd=main_root,
        capture_output=True,
    )
    return finished.returncode == 0


def create_task_worktree(main_root, task):
    target = worktree_path(main_root, task)
    if target.exists():
        return target
    if branch_exists(main_root, task):
        run_git(["worktree", "add", str(target), branch_name(task)], cwd=main_root)
    else:
        run_git(
            ["worktree", "add", "-b", branch_name(task), str(target), "HEAD"],
            cwd=main_root,
        )
    return target


def link_dependencies(main_root, task):
    # Symlinks keep worktrees runnable without reinstalling toolchains.
    target = worktree_path(main_root, task)
    for rel in DEPENDENCY_DIRS:
        origin = main_root / rel
        link = target / rel
        if origin.exists() and not os.path.lexists(link):
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(origin)


def claim_task(task, identity):
    main_root = find_main_root(Path.cwd())
    with board_lock(main_root):
        packet = task_dir(main_root, task)
        if not (packet / "brief.md").exists():
            raise TaskError(f"task {task} is not on the board")
        apply_transition(packet, task, "claim", identity)
        write_board(main_root)
        commit_on_main(
            main_root,
            [f"docs/tasks/{task}/status", "docs/tasks/BOARD.md"],
            f"{task}: claimed by {identity}",
        )
    target = create_task_worktree(main_root, task)
    link_dependencies(main_root, task)
    return target
