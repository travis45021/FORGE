"""Tests for the click-three verification and twin review."""

import pytest

from forge.fas.twin_comparison import comparison_evidence_digest
from forge.fas.verification_presentation import (
    VerificationPresentationError,
    VerificationPresenter,
)


def result(context: str, *, artifact: str = "a") -> dict:
    return {
        "context": context,
        "status": "succeeded",
        "artifact_digest": artifact * 64,
        "warnings": [],
        "authority": {"can_upload": False, "can_start_print": False},
    }


@pytest.fixture
def comparison() -> dict:
    value = {
        "comparison_id": "comparison:1",
        "production": result("production"),
        "twin": result("twin"),
        "differences": [],
        "acceptance": {"status": "matching", "reviewed_by_user": False},
        "can_authorize_production": False,
    }
    value["evidence_digest"] = comparison_evidence_digest(value)
    return value


def test_shows_matching_evidence_warnings_and_limitations(comparison: dict) -> None:
    comparison["production"]["warnings"] = ["A support may be difficult to remove."]
    comparison["evidence_digest"] = comparison_evidence_digest(comparison)
    shown = VerificationPresenter().present(
        comparison, limitations=["Estimate excludes printer warm-up time."]
    )

    assert shown["stage"] == "before_click_three"
    assert shown["can_create_mission"] is True
    assert len(shown["issues"]) == 2
    assert shown["twin_is_advisory"] is True
    assert shown["can_upload"] is False


def test_records_third_click_without_physical_authority(comparison: dict) -> None:
    result = VerificationPresenter().confirm_mission_creation(
        comparison,
        limitations=[],
        actor="user-1",
        reviewed_at="2026-07-26T12:00:00Z",
        confirmation=True,
    )

    assert result["click_number"] == 3
    assert result["reviewed_at"] == "2026-07-26T12:00:00Z"
    assert result["comparison_evidence_digest"] == comparison["evidence_digest"]
    assert result["twin_authority_granted"] is False
    assert result["can_start_print"] is False


def test_difference_removes_create_mission_action(comparison: dict) -> None:
    comparison["differences"] = ["artifact_digest"]
    comparison["acceptance"]["status"] = "different"
    comparison["evidence_digest"] = comparison_evidence_digest(comparison)
    shown = VerificationPresenter().present(comparison, limitations=[])

    assert shown["can_create_mission"] is False
    assert "create_print_mission" not in {action["id"] for action in shown["actions"]}
    with pytest.raises(VerificationPresentationError):
        VerificationPresenter().confirm_mission_creation(
            comparison,
            limitations=[],
            actor="user-1",
            reviewed_at="2026-07-26T12:00:00Z",
            confirmation=True,
        )


def test_rejects_twin_that_claims_authority(comparison: dict) -> None:
    comparison["twin"]["authority"]["can_start_print"] = True

    with pytest.raises(VerificationPresentationError):
        VerificationPresenter().present(comparison, limitations=[])
