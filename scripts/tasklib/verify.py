#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from tasklib.paths import TaskError, find_current_root, run_git, task_dir, utc_now


def extract_verify_command(work_root, task):
    rows = (task_dir(work_root, task) / "brief.md").read_text(encoding="utf-8").splitlines()
    for idx, row in enumerate(rows):
        if row.startswith("## Verify command"):
            break
    else:
        raise TaskError(f"task {task} has no Verify command block")
    fence_at = None
    for pos in range(idx + 1, len(rows)):
        if rows[pos].startswith("```"):
            fence_at = pos
            break
    if fence_at is None:
        raise TaskError(f"task {task} has no Verify command block")
    taken = []
    for row in rows[fence_at + 1 :]:
        if row.startswith("```"):
            break
        taken.append(row)
    else:
        raise TaskError(f"task {task} has no Verify command block")
    block = "\n".join(taken).strip()
    if not block:
        raise TaskError(f"task {task} has no Verify command block")
    return block


def compute_fingerprint(work_root, task):
    # A private index leaves the real one untouched while hashing.
    tmp = tempfile.mkdtemp(prefix="task-fingerprint-")
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = os.path.join(tmp, "index")
    try:
        subprocess.run(
            ["git", "read-tree", "HEAD"], cwd=work_root, env=env,
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "add", "-A", "--", ".",
             f":(exclude)docs/tasks/{task}", ":(exclude).agent-logs"],
            cwd=work_root, env=env, check=True, capture_output=True, text=True,
        )
        # Excludes above skip untracked files only; drop the paths outright
        # so committed verify.log/report.md/transcripts never affect the hash.
        subprocess.run(
            ["git", "rm", "--cached", "-r", "-q", "--ignore-unmatch", "--",
             f"docs/tasks/{task}", ".agent-logs"],
            cwd=work_root, env=env, capture_output=True, text=True,
        )
        done = subprocess.run(
            ["git", "write-tree"], cwd=work_root, env=env,
            check=True, capture_output=True, text=True,
        )
        return done.stdout.strip()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_verify(task):
    work_root = find_current_root(Path.cwd())
    block = extract_verify_command(work_root, task)
    shell = subprocess.run(
        ["bash", "-o", "pipefail", "-c", block],
        cwd=work_root, capture_output=True, text=True,
    )
    checker = str(work_root / "scripts" / "check-standards")
    graded = subprocess.run(
        [sys.executable, checker], cwd=work_root, capture_output=True, text=True
    )
    passed = shell.returncode == 0 and graded.returncode == 0
    lines = [
        f"# verify {task}",
        f"when: {utc_now()}",
        f"root: {work_root}",
        f"head: {run_git(['rev-parse', 'HEAD'], cwd=work_root)}",
        f"fingerprint: {compute_fingerprint(work_root, task)}",
        "",
        "## command",
        block,
        "",
        f"## output (exit {shell.returncode})",
        (shell.stdout + shell.stderr).rstrip(),
        "",
        f"## check-standards (exit {graded.returncode})",
        (graded.stdout + graded.stderr).rstrip(),
        "",
        f"RESULT: {'PASS' if passed else 'FAIL'}",
    ]
    (task_dir(work_root, task) / "verify.log").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return passed


def read_verify_result(work_root, task):
    log = task_dir(work_root, task) / "verify.log"
    if not log.exists():
        return False, ""
    rows = log.read_text(encoding="utf-8").splitlines()
    tree = ""
    for row in rows:
        if row.startswith("fingerprint: "):
            tree = row.split("fingerprint: ", 1)[1].strip()
    return rows[-1] == "RESULT: PASS", tree
