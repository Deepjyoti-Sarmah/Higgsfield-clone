#!/usr/bin/env python3
from conftest import OWNER, TASK, read_status, run_git, run_task


def test_bad_identity_rejected(task_repo):
    done = run_task(task_repo, "claim", TASK, "--as", "no-at-sign")
    assert done.returncode == 1
    assert "invalid identity" in done.stderr
    assert "Traceback" not in done.stderr


def test_task_as_env_used_when_flag_missing(task_repo):
    done = run_task(task_repo, "claim", TASK, extra_env={"TASK_AS": OWNER})
    assert done.returncode == 0, done.stderr
    assert read_status(task_repo, TASK).startswith(f"claimed {OWNER} ")


def test_pathspec_commit_keeps_staged_file(claimed_repo):
    root = claimed_repo
    side = root / "side-note.txt"
    side.write_text("unrelated", encoding="utf-8")
    run_git(root, "add", "--", "side-note.txt")
    assert run_task(root, "say", TASK, "NOTE", "hi", "--as", OWNER).returncode == 0
    staged = run_git(root, "diff", "--cached", "--name-only")
    assert "side-note.txt" in staged.splitlines()
    assert "side-note.txt" not in run_git(root, "log", "--oneline", "--name-only", "-1")


def test_board_noop_commits_nothing_new(claimed_repo):
    root = claimed_repo
    before = run_git(root, "rev-parse", "HEAD")
    assert run_task(root, "board").returncode == 0
    assert run_git(root, "rev-parse", "HEAD") == before


def test_release_reopens_task(claimed_repo):
    root = claimed_repo
    assert run_task(root, "release", TASK, "out of scope", "--as", OWNER).returncode == 0
    assert read_status(root, TASK) == "open"
