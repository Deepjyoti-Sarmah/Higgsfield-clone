#!/usr/bin/env python3
import re

from conftest import OWNER, TASK, add_task, run_task, worktree_of


def test_verify_pass_writes_log(claimed_repo):
    root = claimed_repo
    done = run_task(root, "verify", TASK, cwd=worktree_of(root, TASK))
    assert done.returncode == 0, done.stderr
    assert "RESULT: PASS" in done.stdout
    log = (worktree_of(root, TASK) / "docs" / "tasks" / TASK / "verify.log").read_text(
        encoding="utf-8"
    )
    assert log.splitlines()[-1] == "RESULT: PASS"
    assert "\nfingerprint: " in log
    assert "## check-standards (exit 0)" in log


def test_verify_fail_exits_one(task_repo):
    add_task(task_repo, "T-901", "false")
    assert run_task(task_repo, "claim", "T-901", "--as", OWNER).returncode == 0
    done = run_task(task_repo, "verify", "T-901", cwd=worktree_of(task_repo, "T-901"))
    assert done.returncode == 1
    assert "RESULT: FAIL" in done.stdout
    log = (worktree_of(task_repo, "T-901") / "docs" / "tasks" / "T-901" / "verify.log").read_text(
        encoding="utf-8"
    )
    assert log.splitlines()[-1] == "RESULT: FAIL"


def test_verify_targets_the_main_compose_project(task_repo):
    expected = re.sub(r"[^a-z0-9_-]", "", task_repo.name.lower())
    add_task(task_repo, "T-902", f'test "$COMPOSE_PROJECT_NAME" = "{expected}"')
    assert run_task(task_repo, "claim", "T-902", "--as", OWNER).returncode == 0
    done = run_task(task_repo, "verify", "T-902", cwd=worktree_of(task_repo, "T-902"))
    assert "RESULT: PASS" in done.stdout, done.stdout
