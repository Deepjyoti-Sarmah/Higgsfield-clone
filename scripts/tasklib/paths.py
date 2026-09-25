#!/usr/bin/env python3
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class TaskError(Exception):
    pass


# Symlinked into worktrees so verify works without a reinstall.
DEPENDENCY_DIRS = ("apps/web/node_modules", "apps/api/.venv")


def run_git(prog_args, cwd):
    finished = subprocess.run(
        ["git", *prog_args], cwd=cwd, capture_output=True, text=True
    )
    if finished.returncode:
        raise TaskError(finished.stderr.strip() or f"git {' '.join(prog_args)} failed")
    return finished.stdout.strip()


def find_main_root(from_path):
    listed = run_git(["worktree", "list", "--porcelain"], cwd=from_path)
    for row in listed.splitlines():
        if row.startswith("worktree "):
            return Path(row.split(" ", 1)[1])
    raise TaskError("not inside a git worktree")


def find_current_root(from_path):
    return Path(run_git(["rev-parse", "--show-toplevel"], cwd=from_path))


def task_dir(root, task):
    return root / "docs" / "tasks" / task


def worktree_path(root, task):
    return root / ".worktrees" / task


def branch_name(task):
    return f"task/{task}"


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
