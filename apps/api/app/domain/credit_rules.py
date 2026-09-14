from typing import Literal

GUEST_GRANT_CREDITS = 60
TOPUP_CREDITS = 100
VIDEO_CREDIT_COST = 20
MAX_STEP_ATTEMPTS = 2

GUEST_PER_IP_DAILY = 5
USER_DAILY_JOBS = 10
TOPUP_DAILY_LIMIT = 2
PAID_VIDEO_COST_CENTS = 25
PAID_IMAGE_COST_CENTS = 8
PAID_BACKENDS: tuple[str, ...] = ("modal", "openrouter")

LedgerKind = Literal["GRANT", "HOLD", "SETTLE", "RELEASE", "TOPUP"]


def hold_amount(cost: int) -> int:
    return -cost


def release_amount(cost: int) -> int:
    return cost
