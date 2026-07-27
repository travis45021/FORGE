"""Application composition tests for the governed upload path."""

from unittest.mock import Mock

import pytest

from forge.fas.print_dispatch import PrintDispatchCoordinator


def call(coordinator: PrintDispatchCoordinator) -> dict:
    return coordinator.dispatch_confirmed_upload(
        mission={"mission_id": "mission:1"},
        job={"job_id": "job:1"},
        acceptance={"artifact_digest": "a" * 64},
        authorization={"outcome": "allow"},
        capability={
            "capability_id": "artifact.upload",
            "provider_id": "provider:custom",
        },
        context_id="context:1",
        command_id="command:1",
        resource_ids=["resource:printer"],
        command_expires_at="2026-07-26T12:05:20Z",
        evaluated_at="2026-07-26T12:05:00Z",
        provider_evidence={"evidence_digest": "b" * 64},
        runtime_lease_active=True,
        authorization_verified=True,
    )


def test_composes_existing_guards_without_claiming_print_outcome() -> None:
    calls: list[str] = []
    executive = Mock()
    transport = Mock()
    runtime = Mock()
    executive.prepare_confirmed_artifact_execution.side_effect = lambda *args: (
        calls.append("executive") or {"payload": {"job_id": "job:1"}}
    )
    transport.prepare_artifact_upload.side_effect = lambda *args, **kwargs: (
        calls.append("transport")
        or {
            "provider_id": "provider:custom",
            "job_id": "job:1",
            "artifact_digest": "a" * 64,
            "comparison_id": "comparison:1",
            "comparison_evidence_digest": "b" * 64,
            "comparison_reviewed_by": "reviewer:1",
            "comparison_reviewed_at": "2026-07-26T12:00:00Z",
            "input_digest": "c" * 64,
            "profile_digest": "d" * 64,
            "engine_source_digest": "e" * 64,
            "engine_build_digest": "f" * 64,
            "confirmed_by": "user:1",
            "confirmed_at": "2026-07-26T12:04:00Z",
            "confirmation_expires_at": "2026-07-26T12:09:00Z",
            "confirmation_token": "secret-confirmation-token",
            "final_confirmation_evidence": {
                "confirmation_token": "secret-confirmation-token"
            },
            "final_confirmation_evidence_digest": "1" * 64,
            "live_checks_checked_at": "2026-07-26T12:03:00Z",
            "live_checks_expires_at": "2026-07-26T12:08:00Z",
            "live_checks_evidence_digest": "2" * 64,
            "fourth_click_satisfied": True,
            "physical_dispatch_allowed": False,
        }
    )
    runtime.dispatch_artifact_upload.side_effect = lambda *args, **kwargs: (
        calls.append("runtime")
        or {"status": "dispatched", "physical_outcome_confirmed": False}
    )

    result = call(
        PrintDispatchCoordinator(
            executive=executive,
            transport=transport,
            runtime=runtime,
        )
    )

    assert calls == ["executive", "transport", "runtime"]
    assert result["upload_dispatched"] is True
    assert result["print_started"] is False
    assert result["physical_outcome_confirmed"] is False
    assert result["upload_evidence"]["fourth_click_satisfied"] is True
    assert "prepared_upload" not in result
    assert "confirmation_token" not in result["upload_evidence"]
    assert "final_confirmation_evidence" not in result["upload_evidence"]


def test_stops_before_transport_when_executive_rejects() -> None:
    executive = Mock()
    transport = Mock()
    runtime = Mock()
    executive.prepare_confirmed_artifact_execution.side_effect = ValueError(
        "executive blocked"
    )
    coordinator = PrintDispatchCoordinator(
        executive=executive,
        transport=transport,
        runtime=runtime,
    )

    with pytest.raises(ValueError, match="executive blocked"):
        call(coordinator)

    transport.prepare_artifact_upload.assert_not_called()
    runtime.dispatch_artifact_upload.assert_not_called()
