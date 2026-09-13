from app.domain.credit_rules import (
    GUEST_GRANT_CREDITS,
    MAX_STEP_ATTEMPTS,
    VIDEO_CREDIT_COST,
    hold_amount,
    release_amount,
)
from app.domain.job_states import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATUSES,
    can_transition,
    statuses_allowed_before,
)
from app.domain.preset_catalog import PRESET_CATALOG


def test_every_allowed_transition_is_permitted() -> None:
    for from_status, targets in ALLOWED_TRANSITIONS.items():
        for to_status in targets:
            assert can_transition(from_status, to_status)


def test_sample_of_disallowed_transitions_is_rejected() -> None:
    assert not can_transition("queued", "succeeded")
    assert not can_transition("queued", "queued")
    assert not can_transition("running", "running")
    assert not can_transition("succeeded", "running")
    assert not can_transition("succeeded", "failed")
    assert not can_transition("failed", "queued")


def test_statuses_allowed_before_each_target() -> None:
    assert statuses_allowed_before("running") == {"queued"}
    assert statuses_allowed_before("succeeded") == {"running"}
    assert statuses_allowed_before("failed") == {"queued", "running"}
    assert statuses_allowed_before("queued") == {"running"}


def test_terminal_statuses_are_succeeded_and_failed() -> None:
    assert TERMINAL_STATUSES == {"succeeded", "failed"}


def test_catalog_has_twelve_unique_slugs_in_order() -> None:
    slugs = [preset.slug for preset in PRESET_CATALOG]

    assert len(slugs) == 12
    assert len(set(slugs)) == 12
    assert [preset.sort_order for preset in PRESET_CATALOG] == list(range(1, 13))


def test_catalog_has_three_categories() -> None:
    assert {preset.category for preset in PRESET_CATALOG} == {"camera", "cinematic", "dynamic"}


def test_every_preset_costs_twenty_credits() -> None:
    assert VIDEO_CREDIT_COST == 20
    assert all(preset.credit_cost == VIDEO_CREDIT_COST for preset in PRESET_CATALOG)


def test_credit_rules_numbers_and_helpers() -> None:
    assert GUEST_GRANT_CREDITS == 60
    assert MAX_STEP_ATTEMPTS == 2
    assert hold_amount(VIDEO_CREDIT_COST) == -VIDEO_CREDIT_COST
    assert release_amount(VIDEO_CREDIT_COST) == VIDEO_CREDIT_COST
