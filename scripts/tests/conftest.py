#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ORIGIN = Path(__file__).resolve().parents[2]
OWNER = "tester@harness"
REVIEWER = "reviewer@claude-code"
TASK = "T-900"
BRIEF = "# T-900: throwaway fixture task\n\n## Verify command\n```\ntrue\n```\n"


def run_git(root, *prog_args):
    done = subprocess.run(
        ["git", *prog_args], cwd=root, capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def run_task(root, *cli_args, cwd=None, extra_env=None):
    env = dict(os.environ)
    env.pop("TASK_AS", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "task"), *cli_args],
        cwd=str(cwd or root),
        capture_output=True,
        text=True,
        env=env,
    )


def add_task(root, name, command):
    packet = root / "docs" / "tasks" / name
    packet.mkdir(parents=True, exist_ok=True)
    brief = f"# {name}: throwaway fixture task\n\n## Verify command\n```\n{command}\n```\n"
    (packet / "brief.md").write_text(brief, encoding="utf-8")
    (packet / "status").write_text("open\n", encoding="utf-8")
    run_git(root, "add", "-A")
    run_git(root, "commit", "--quiet", "-m", f"{name}: seed")


def read_status(root, name):
    return (root / "docs" / "tasks" / name / "status").read_text(encoding="utf-8").strip()


def worktree_of(root, name):
    return root / ".worktrees" / name


@pytest.fixture
def task_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    run_git(root, "init", "-b", "main")
    run_git(root, "config", "user.email", "tester@example.com")
    run_git(root, "config", "user.name", "tester")
    shutil.copytree(ORIGIN / "scripts", root / "scripts")
    hooks = root / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    shutil.copy(ORIGIN / ".claude" / "hooks" / "capture.py", hooks / "capture.py")
    (root / "docs" / "tasks" / TASK).mkdir(parents=True)
    (root / "docs" / "tasks" / TASK / "brief.md").write_text(BRIEF, encoding="utf-8")
    (root / "docs" / "tasks" / TASK / "status").write_text("open\n", encoding="utf-8")
    run_git(root, "add", "-A")
    run_git(root, "commit", "--quiet", "-m", "seed")
    return root


@pytest.fixture
def claimed_repo(task_repo):
    done = run_task(task_repo, "claim", TASK, "--as", OWNER)
    assert done.returncode == 0, done.stderr
    return task_repo
