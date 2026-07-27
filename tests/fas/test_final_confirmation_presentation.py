"""Tests for the mandatory Yes, Print interface contract."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from forge.fas.final_confirmation_presentation import (
    FinalConfirmationPresentationError,
    FinalConfirmationPresenter,
)
from forge.fas.live_printer_checks import (
    REQUIRED_CHECKS,
    LivePrinterCheckService,
    live_check_evidence_digest,
)

ROOT = Path(__file__).resolve().parents[2]


def evidence(*, failed: str | None = None) -> dict:
    checks = {name: True for name in REQUIRED_CHECKS}
    if failed:
        checks[failed] = False
    return LivePrinterCheckService().evaluate(
        provider_id="provider:user-built",
        artifact_digest="a" * 64,
        checks=checks,
        checked_at="2026-07-26T12:04:00Z",
        expires_at="2026-07-26T12:09:00Z",
    )


def show(live: dict) -> dict:
    return FinalConfirmationPresenter().present(
        live,
        printer_name="Workshop printer",
        job_name="Bracket",
        presented_at="2026-07-26T12:05:00Z",
    )


def test_shows_yes_print_only_after_all_live_checks_pass() -> None:
    result = show(evidence())

    assert result["stage"] == "before_click_four"
    assert result["confirmation_label"] == "Yes, Print"
    assert result["confirmation_is_fourth_click"] is True
    assert result["bypass_enabled"] is False
    assert result["can_upload"] is False


def test_records_fourth_click_without_dispatching() -> None:
    result = FinalConfirmationPresenter().confirm(
        evidence(),
        printer_name="Workshop printer",
        job_name="Bracket",
        actor="user-1",
        action="yes_print",
        presented_at="2026-07-26T12:05:00Z",
    )

    assert result["click_number"] == 4
    assert result["action"] == "Yes, Print"
    assert result["requires_controlled_upload"] is True
    assert result["physical_dispatch_allowed"] is False


def test_record_and_example_match_strict_non_authoritative_schema() -> None:
    schema = json.loads(
        (ROOT / "schemas/fas/fourth-click-presentation-record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    example = json.loads(
        (ROOT / "examples/fas/fourth-click-presentation-record.example.json").read_text(
            encoding="utf-8"
        )
    )
    generated = FinalConfirmationPresenter().confirm(
        evidence(),
        printer_name="Workshop printer",
        job_name="Bracket",
        actor="user-1",
        action="yes_print",
        presented_at="2026-07-26T12:05:00Z",
    )
    validator = Draft202012Validator(schema)
    Draft202012Validator.check_schema(schema)
    validator.validate(generated)
    validator.validate(example)

    example["physical_dispatch_allowed"] = True
    with pytest.raises(ValidationError):
        validator.validate(example)


@pytest.mark.parametrize("failed", sorted(REQUIRED_CHECKS))
def test_each_failed_or_stale_check_removes_yes_print(failed: str) -> None:
    result = show(evidence(failed=failed))

    assert result["can_confirm"] is False
    assert "yes_print" not in {action["id"] for action in result["actions"]}
    with pytest.raises(FinalConfirmationPresentationError):
        FinalConfirmationPresenter().confirm(
            evidence(failed=failed),
            printer_name="Workshop printer",
            job_name="Bracket",
            actor="user-1",
            action="yes_print",
            presented_at="2026-07-26T12:05:00Z",
        )


def test_rejects_live_evidence_that_claims_upload_authority() -> None:
    live = evidence()
    live["can_upload"] = True

    with pytest.raises(FinalConfirmationPresentationError):
        show(live)


def test_rejects_expired_or_not_yet_checked_evidence() -> None:
    for presented_at in (
        "2026-07-26T12:03:59Z",
        "2026-07-26T12:09:00Z",
    ):
        with pytest.raises(FinalConfirmationPresentationError):
            FinalConfirmationPresenter().present(
                evidence(),
                printer_name="Workshop printer",
                job_name="Bracket",
                presented_at=presented_at,
            )


def test_rejects_mutated_or_extra_live_evidence() -> None:
    mutated = evidence()
    mutated["checks"]["connected"] = False
    with pytest.raises(FinalConfirmationPresentationError, match="digest"):
        show(mutated)

    extra = evidence()
    extra["confirmation_token"] = "must-not-render"
    with pytest.raises(FinalConfirmationPresentationError, match="fields"):
        show(extra)


def test_rejects_inconsistent_pass_claim() -> None:
    live = evidence(failed="connected")
    live["passed"] = True
    live["evidence_digest"] = live_check_evidence_digest(live)

    with pytest.raises(FinalConfirmationPresentationError, match="pass evidence"):
        show(live)
