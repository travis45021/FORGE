"""Tests for the immutable v1 final-confirmation policy."""

from itertools import product

import pytest

from forge.fas.final_confirmation_policy import (
    V1_EXPERIENCE_MODES,
    V1_GOVERNANCE_ROLES,
    FinalConfirmationPolicy,
    FinalConfirmationPolicyError,
)


def test_every_released_role_and_mode_requires_fourth_click() -> None:
    policy = FinalConfirmationPolicy()

    for role, mode in product(V1_GOVERNANCE_ROLES, V1_EXPERIENCE_MODES):
        decision = policy.evaluate(role=role, mode=mode)

        assert decision["required_clicks"] == 4
        assert decision["final_confirmation_required"] is True
        assert decision["bypass_enabled"] is False


@pytest.mark.parametrize(
    ("role", "mode"),
    [
        ("owner", "simple_local"),
        ("end_user", "autonomous_path"),
        ("", "offline_manual"),
    ],
)
def test_unknown_roles_and_modes_fail_closed(role: str, mode: str) -> None:
    with pytest.raises(FinalConfirmationPolicyError):
        FinalConfirmationPolicy().evaluate(role=role, mode=mode)
