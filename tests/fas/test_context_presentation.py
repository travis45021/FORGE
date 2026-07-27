"""Tests for the user-controlled second-click print-context review."""

import pytest

from forge.fas.context_presentation import (
    ContextPresentationError,
    PrintContextPresenter,
)


@pytest.fixture
def context() -> dict:
    return {
        "context_id": "context:print-1",
        "source_digest": "a" * 64,
        "printer": {
            "provider_id": "provider:user-built",
            "display_name": "Workshop printer",
            "capabilities": ["fff.extrusion", "artifact.upload"],
            "source": "local capability provider",
        },
        "material": {"name": "PLA", "source": "3MF metadata"},
        "process": {"name": "0.20 mm quality", "source": "local profile"},
        "safety": {"status": "passed", "summary": "Local safety checks passed."},
        "assumptions": ["The installed nozzle is 0.4 mm."],
        "missing_information": [],
    }


def test_shows_context_before_click_two_without_authority(context: dict) -> None:
    result = PrintContextPresenter().present(context)

    assert result["stage"] == "before_click_two"
    assert result["sections"]["printer"]["provider_id"] == "provider:user-built"
    assert result["can_confirm"] is True
    assert result["user_confirmation_required"] is True
    assert result["can_slice"] is False
    assert result["can_start_print"] is False


def test_records_explicit_second_click_without_authority(context: dict) -> None:
    result = PrintContextPresenter().confirm(context, actor="user-1", confirmation=True)

    assert result["click_number"] == 2
    assert result["confirmed_by"] == "user-1"
    assert result["can_authorize_production"] is False


def test_missing_information_blocks_confirmation(context: dict) -> None:
    context["missing_information"] = ["Select a build plate."]
    result = PrintContextPresenter().present(context)

    assert result["can_confirm"] is False
    assert "confirm_context" not in {action["id"] for action in result["actions"]}
    with pytest.raises(ContextPresentationError):
        PrintContextPresenter().confirm(context, actor="user-1", confirmation=True)


def test_unreviewed_safety_blocks_confirmation(context: dict) -> None:
    context["safety"]["status"] = "needs_review"

    with pytest.raises(ContextPresentationError):
        PrintContextPresenter().confirm(context, actor="user-1", confirmation=True)
