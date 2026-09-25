#!/usr/bin/env python3
from conftest import OWNER, REVIEWER, TASK, read_status, run_git, run_task, worktree_of


def fresh_verified(root):
    tree = worktree_of(root, TASK)
    assert run_task(root, "verify", TASK, cwd=tree).returncode == 0
    return tree


def test_submit_without_report_refused(claimed_repo):
    root = claimed_repo
    tree = worktree_of(root, TASK)
    run_task(root, "verify", TASK, cwd=tree)
    done = run_task(root, "submit", TASK, "--as", OWNER, "--transcript", "t.txt", cwd=tree)
    assert done.returncode == 1
    assert "report.md" in done.stderr


def test_submit_stale_fingerprint_refused(claimed_repo, tmp_path):
    root = claimed_repo
    tree = fresh_verified(root)
    (tree / "docs" / "tasks" / TASK / "report.md").write_text("# Report\n", encoding="utf-8")
    marvel = tmp_path / "transcript.txt"
    marvel.write_text("did the work", encoding="utf-8")
    (tree / "stale.txt").write_text("changed after verify", encoding="utf-8")
    done = run_task(root, "submit", TASK, "--as", OWNER, "--transcript", str(marvel), cwd=tree)
    assert done.returncode == 1
    assert "code changed since verify" in done.stderr


def test_submit_without_transcript_refused(claimed_repo):
    root = claimed_repo
    tree = fresh_verified(root)
    (tree / "docs" / "tasks" / TASK / "report.md").write_text("# Report\n", encoding="utf-8")
    done = run_task(root, "submit", TASK, "--as", OWNER, cwd=tree)
    assert done.returncode == 1
    assert "--transcript is required" in done.stderr


def test_submit_success_commits_and_copies_log(claimed_repo, tmp_path):
    root = claimed_repo
    tree = fresh_verified(root)
    (tree / "docs" / "tasks" / TASK / "report.md").write_text("# Report\n", encoding="utf-8")
    marvel = tmp_path / "transcript.txt"
    marvel.write_text("did the work", encoding="utf-8")
    done = run_task(root, "submit", TASK, "--as", OWNER, "--transcript", str(marvel), cwd=tree)
    assert done.returncode == 0, done.stderr
    assert f"submit by {OWNER}" in run_git(tree, "log", "--oneline", "-1")
    assert list((tree / ".agent-logs").glob("*.md"))
    assert read_status(root, TASK).startswith("submitted ")
    thread = (root / "docs" / "tasks" / TASK / "thread.md").read_text(encoding="utf-8")
    assert "submitted at" in thread


def test_review_cycle_and_release_guard(claimed_repo, tmp_path):
    root = claimed_repo
    tree = fresh_verified(root)
    (tree / "docs" / "tasks" / TASK / "report.md").write_text("# Report\n", encoding="utf-8")
    marvel = tmp_path / "transcript.txt"
    marvel.write_text("did the work", encoding="utf-8")
    assert run_task(root, "submit", TASK, "--as", OWNER, "--transcript", str(marvel), cwd=tree).returncode == 0
    assert run_task(root, "review", TASK, "changes", "fix it", "--as", REVIEWER).returncode == 0
    assert read_status(root, TASK).startswith("changes-requested ")
    assert run_task(root, "submit", TASK, "--as", OWNER, "--transcript", str(marvel), cwd=tree).returncode == 0
    assert run_task(root, "review", TASK, "accept", "good", "--as", REVIEWER).returncode == 0
    assert read_status(root, TASK).startswith("accepted ")
    thread = (root / "docs" / "tasks" / TASK / "thread.md").read_text(encoding="utf-8")
    assert "CHANGES REQUESTED" in thread
    assert "ACCEPTED" in thread
    failed = run_task(root, "release", TASK, "never mind", "--as", REVIEWER)
    assert failed.returncode == 1
    assert "cannot release" in failed.stderr
