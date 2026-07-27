"""Fail-closed v1 policy for the final physical print confirmation."""

from __future__ import annotations

from typing import Final


class FinalConfirmationPolicyError(ValueError):
    """Raised when final-confirmation policy inputs are not released in v1."""


V1_EXPERIENCE_MODES: Final[tuple[str, ...]] = (
    "offline_manual",
    "simple_local",
    "custom_builder",
)
V1_GOVERNANCE_ROLES: Final[tuple[str, ...]] = (
    "end_user",
    "forge_admin",
    "forge_architect",
    "ai_council",
    "sentinel",
)


class FinalConfirmationPolicy:
    """Reports the immutable v1 requirement for the fourth user click."""

    def evaluate(self, *, role: str, mode: str) -> dict[str, object]:
        """Return the released policy without granting bypass authority."""
        if role not in V1_GOVERNANCE_ROLES:
            raise FinalConfirmationPolicyError("unknown v1 governance role")
        if mode not in V1_EXPERIENCE_MODES:
            raise FinalConfirmationPolicyError("unknown v1 experience mode")
        return {
            "schema_version": "1.0.0",
            "role": role,
            "mode": mode,
            "required_clicks": 4,
            "final_confirmation_required": True,
            "bypass_enabled": False,
        }
