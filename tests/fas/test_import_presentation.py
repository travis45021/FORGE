"""Tests for plain-language import status and ambiguity resolution."""

import pytest

from forge.fas.import_presentation import (
    ImportPresentationError,
    ImportStatusPresenter,
)


def assessment(*, decision: str = "accepted") -> dict:
    ambiguities = (
        [] if decision == "accepted" else ["3MF build instructions are missing"]
    )
    return {
        "assessment_id": "sha256:" + ("a" * 64),
        "format": "3mf",
        "quarantine": {"isolated": True},
        "decision": decision,
        "ambiguities": ambiguities,
        "can_authorize_production": False,
    }


def test_presents_accepted_file_without_granting_authority() -> None:
    result = ImportStatusPresenter().present(assessment())

    assert result["heading"] == "File checks passed"
    assert result["can_continue"] is True
    assert result["can_slice"] is False
    assert result["can_upload"] is False
    assert result["plain_language"] is True
    assert result["non_color_cue"] == "check"


def test_presents_ambiguity_with_user_controlled_choices() -> None:
    result = ImportStatusPresenter().present(
        assessment(decision="needs_user_resolution")
    )

    assert result["resolution_required"] is True
    assert result["can_continue"] is False
    assert result["issues"][0]["accessible_label"].startswith("File issue:")
    assert {action["id"] for action in result["actions"]} == {
        "open_builder",
        "replace_file",
        "cancel_import",
    }


def test_resolution_never_overrides_ambiguity() -> None:
    result = ImportStatusPresenter().record_resolution(
        assessment(decision="needs_user_resolution"),
        action="open_builder",
        actor="user-1",
    )

    assert result["status"] == "awaiting_builder_review"
    assert result["ambiguity_overridden"] is False
    assert result["can_authorize_production"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("can_authorize_production", True),
        ("ambiguities", [42]),
        ("decision", "silently_accepted"),
    ],
)
def test_rejects_unsafe_or_invalid_evidence(field: str, value: object) -> None:
    item = assessment()
    item[field] = value

    with pytest.raises(ImportPresentationError):
        ImportStatusPresenter().present(item)
