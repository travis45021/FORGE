"""Tests for one accessible FORGE print interface across every v1 mode."""

import pytest

from forge.fas.interfaces import INTERFACE_MODES, InterfaceError, InterfaceGateway


@pytest.fixture
def gateway() -> InterfaceGateway:
    return InterfaceGateway(lambda request: {"received": request["request_id"]})


@pytest.fixture
def presentation() -> dict:
    return {
        "heading": "Review your print setup",
        "summary": "Check the printer, material, process, and safety context.",
        "actions": [
            {"id": "confirm_context", "label": "Use this setup"},
            {"id": "cancel", "label": "Cancel"},
        ],
        "plain_language": True,
        "accessible_label": "Print setup ready for your confirmation",
        "non_color_cue": "check",
        "can_upload": False,
        "can_start_print": False,
    }


def test_every_mode_has_the_same_core_workflow(
    gateway: InterfaceGateway, presentation: dict
) -> None:
    screens = [
        gateway.print_workflow_screen("confirm_context", presentation, mode=mode)
        for mode in sorted(INTERFACE_MODES)
    ]

    action_sets = [[action["id"] for action in screen["actions"]] for screen in screens]
    assert all(actions == action_sets[0] for actions in action_sets)
    assert all(screen["interface"] == "forge" for screen in screens)
    assert all(screen["separate_slicer_interface"] is False for screen in screens)
    assert all(screen["keyboard_operable"] is True for screen in screens)
    assert all(screen["screen_reader_state"] is True for screen in screens)
    assert all(screen["can_upload"] is False for screen in screens)


def test_structured_errors_keep_actionable_parity(gateway: InterfaceGateway) -> None:
    errors = [
        gateway.print_workflow_error(
            screen_id="add_file",
            reason="unsafe_archive_path",
            summary="The 3MF file contains an unsafe path.",
            affected_object="uploaded file",
            next_step="Choose a corrected file.",
            mode=mode,
            safety_impact="import_blocked",
        )
        for mode in sorted(INTERFACE_MODES)
    ]

    assert all(error["error"]["recommended_next_step"] for error in errors)
    assert all(error["accessible_label"].startswith("Error:") for error in errors)
    assert all(error["non_color_cue"] == "error" for error in errors)
    assert all(error["core_workflow_parity"] is True for error in errors)


def test_rejects_interface_presentations_that_claim_authority(
    gateway: InterfaceGateway, presentation: dict
) -> None:
    presentation["can_upload"] = True

    with pytest.raises(InterfaceError):
        gateway.print_workflow_screen("confirm_context", presentation)
