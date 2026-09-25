#!/usr/bin/env python3
import contextlib
import fcntl
import os
from dataclasses import dataclass
from pathlib import Path

from tasklib.paths import TaskError, run_git, utc_now


STATES = ("open", "claimed", "blocked", "submitted", "changes-requested", "accepted")

# The only allowed moves; every transition goes through apply_transition.
MOVES = {
    "claim": (("open",), "claimed"),
    "block": (("claimed", "changes-requested"), "blocked"),
    "unblock": (("blocked",), "claimed"),
    "submit": (("claimed", "changes-requested"), "submitted"),
    "accept": (("submitted",), "accepted"),
    "request-changes": (("submitted",), "changes-requested"),
    "release": (
        ("open", "claimed", "blocked", "submitted", "changes-requested"),
        "open",
    ),
}


@dataclass
class Status:
    state: str
    owner: str
    since: str


def parse_status(task, line):
    bits = line.strip().split()
    if bits == ["open"]:
        return Status("open", "", "")
    if len(bits) == 3 and bits[0] in STATES and "@" in bits[1]:
        return Status(bits[0], bits[1], bits[2])
    raise TaskError(f"task {task} has a corrupt status line")


def read_status(packet, task):
    seen = packet / "status"
    if not seen.exists():
        raise TaskError(f"task {task} is not on the board")
    return parse_status(task, seen.read_text(encoding="utf-8"))


def apply_transition(packet, task, action, owner):
    current = read_status(packet, task)
    allowed, target = MOVES[action]
    if current.state not in allowed:
        raise TaskError(f"cannot {action} {task}: it is '{current.state}'")
    if target == "open":
        (packet / "status").write_text("open\n", encoding="utf-8")
    elif current.state == "open":
        (packet / "status").write_text(
            f"{target} {owner} {utc_now()}\n", encoding="utf-8"
        )
    else:
        # The claimant stays the owner; later moves only refresh the time.
        (packet / "status").write_text(
            f"{target} {current.owner} {utc_now()}\n", encoding="utf-8"
        )
    return target


@contextlib.contextmanager
def board_lock(main_root):
    # One lock file serialises board writers across harnesses.
    raw = run_git(["rev-parse", "--git-common-dir"], cwd=main_root)
    git_dir = Path(raw) if os.path.isabs(raw) else main_root / raw
    git_dir.mkdir(parents=True, exist_ok=True)
    with open(git_dir / "task-board.lock", "a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def commit_on_main(main_root, rel_paths, message):
    # Pathspec commits keep unrelated staged work untouched.
    run_git(["add", "--", *rel_paths], cwd=main_root)
    run_git(["commit", "--quiet", "-m", message, "--", *rel_paths], cwd=main_root)
