"""Tests for honest post-confirmation upload status presentation."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from forge.fas.dispatch_presentation import (
    DispatchOutcomePresenter,
    DispatchPresentationError,
)
from forge.fas.interfaces import InterfaceGateway

ROOT = Path(__file__).resolve().parents[2]


def dispatch_result() -> dict:
    return {
        "upload_evidence": {
            "provider_id": "provider:custom",
            "job_id": "job:1",
            "artifact_digest": "a" * 64,
            "final_confirmation_evidence_digest": "b" * 64,
            "fourth_click_satisfied": True,
            "physical_dispatch_allowed": False,
        },
        "runtime_result": {
            "status": "dispatched",
            "provider_id": "provider:custom",
            "job_id": "job:1",
            "artifact_digest": "a" * 64,
            "physical_outcome_confirmed": False,
            "provider_dispatch_evidence_digest": "c" * 64,
        },
        "upload_dispatched": True,
        "print_started": False,
        "physical_outcome_confirmed": False,
    }


def test_presents_dispatch_without_claiming_printer_success() -> None:
    result = DispatchOutcomePresenter().present(dispatch_result())

    assert result["upload_command_dispatched"] is True
    assert result["printer_receipt_confirmed"] is False
    assert result["print_started"] is False
    assert result["start_control_enabled"] is False
    assert result["can_start_print"] is False
    assert "not yet confirmed" in result["summary"]


def test_dispatch_status_uses_the_unified_interface_contract() -> None:
    presentation = DispatchOutcomePresenter().present(dispatch_result())
    screen = InterfaceGateway(lambda request: request).print_workflow_screen(
        "print_dispatch_status",
        presentation,
        mode="accessible",
    )

    assert screen["separate_slicer_interface"] is False
    assert screen["core_workflow_parity"] is True
    assert screen["can_start_print"] is False


def test_generated_and_published_presentations_match_strict_schema() -> None:
    contract = json.loads(
        (ROOT / "schemas/fas/dispatch-status-presentation.schema.json").read_text(
            encoding="utf-8"
        )
    )
    example = json.loads(
        (ROOT / "examples/fas/dispatch-status-presentation.example.json").read_text(
            encoding="utf-8"
        )
    )
    generated = DispatchOutcomePresenter().present(dispatch_result())
    validator = Draft202012Validator(contract)

    Draft202012Validator.check_schema(contract)
    validator.validate(example)
    validator.validate(generated)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("confirmation_token", "secret"),
        ("printer_receipt_confirmed", True),
        ("print_started", True),
        ("start_control_enabled", True),
    ],
)
def test_schema_rejects_secret_or_overstated_status(field: str, value) -> None:
    contract = json.loads(
        (ROOT / "schemas/fas/dispatch-status-presentation.schema.json").read_text(
            encoding="utf-8"
        )
    )
    example = json.loads(
        (ROOT / "examples/fas/dispatch-status-presentation.example.json").read_text(
            encoding="utf-8"
        )
    )
    example[field] = value

    with pytest.raises(ValidationError):
        Draft202012Validator(contract).validate(example)


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("root", "print_started", True),
        ("root", "physical_outcome_confirmed", True),
        ("runtime_result", "status", "completed"),
        ("runtime_result", "physical_outcome_confirmed", True),
        ("upload_evidence", "physical_dispatch_allowed", True),
    ],
)
def test_rejects_overstated_or_inconsistent_outcomes(
    section: str, field: str, value
) -> None:
    item = deepcopy(dispatch_result())
    target = item if section == "root" else item[section]
    target[field] = value

    with pytest.raises(DispatchPresentationError):
        DispatchOutcomePresenter().present(item)


@pytest.mark.parametrize(
    "secret_field",
    ["confirmation_token", "final_confirmation_evidence"],
)
def test_rejects_secret_confirmation_material(secret_field: str) -> None:
    item = dispatch_result()
    item["upload_evidence"][secret_field] = "secret"

    with pytest.raises(DispatchPresentationError):
        DispatchOutcomePresenter().present(item)


@pytest.mark.parametrize("field", ["provider_id", "job_id", "artifact_digest"])
def test_rejects_runtime_identity_mismatch(field: str) -> None:
    item = dispatch_result()
    item["runtime_result"][field] = "different"

    with pytest.raises(DispatchPresentationError, match="does not match"):
        DispatchOutcomePresenter().present(item)


@pytest.mark.parametrize(
    ("section", "field"),
    [
        ("upload_evidence", "artifact_digest"),
        ("upload_evidence", "final_confirmation_evidence_digest"),
        ("runtime_result", "provider_dispatch_evidence_digest"),
    ],
)
def test_rejects_invalid_presentation_digests(section: str, field: str) -> None:
    item = dispatch_result()
    item[section][field] = "not-a-digest"

    with pytest.raises(DispatchPresentationError, match="digest"):
        DispatchOutcomePresenter().present(item)
