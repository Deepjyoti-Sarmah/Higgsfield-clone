from typing import Literal

JobStatus = Literal["queued", "running", "succeeded", "failed"]

TERMINAL_STATUSES: frozenset[JobStatus] = frozenset({"succeeded", "failed"})

ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    "queued": frozenset({"running", "failed"}),
    "running": frozenset({"succeeded", "failed", "queued"}),
    "succeeded": frozenset(),
    "failed": frozenset(),
}


def can_transition(from_status: JobStatus, to_status: JobStatus) -> bool:
    return to_status in ALLOWED_TRANSITIONS.get(from_status, frozenset())


def statuses_allowed_before(to_status: JobStatus) -> frozenset[JobStatus]:
    return frozenset(status for status, allowed in ALLOWED_TRANSITIONS.items() if to_status in allowed)
