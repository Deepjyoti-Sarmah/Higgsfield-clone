from typing import Literal

GUEST_GRANT_CREDITS = 60
VIDEO_CREDIT_COST = 20
MAX_STEP_ATTEMPTS = 2

LedgerKind = Literal["GRANT", "HOLD", "SETTLE", "RELEASE", "TOPUP"]


def hold_amount(cost: int) -> int:
    return -cost


def release_amount(cost: int) -> int:
    return cost
