"""Tests for accepted artifact integration with the FORGE Executive."""

from copy import deepcopy

import pytest

from forge.fas.executive import ExecutiveError, ForgeExecutive


@pytest.fixture
def inputs() -> dict[str, dict]:
    digest = "a" * 64
    input_digest = "b" * 64
    profile_digest = "c" * 64
    engine_source_digest = "d" * 64
    engine_build_digest = "e" * 64
    comparison_digest = "f" * 64
    return {
        "mission": {
            "mission_id": "mission:print-1",
            "state": "approved",
            "correlation_id": "job-1",
            "context": {
                "job_id": "job-1",
                "artifact_digest": digest,
                "input_digest": input_digest,
                "profile_digest": profile_digest,
                "engine_source_digest": engine_source_digest,
                "engine_build_digest": engine_build_digest,
                "comparison_id": "comparison-1",
                "comparison_evidence_digest": comparison_digest,
            },
            "plan": [{"capability_id": "artifact.upload"}],
        },
        "job": {
            "job_id": "job-1",
            "provider_id": "provider:custom",
            "state": "upload_pending",
            "click_count": 3,
            "artifact_digest": digest,
            "input_digest": input_digest,
            "profile_digest": profile_digest,
            "engine_source_digest": engine_source_digest,
            "engine_build_digest": engine_build_digest,
            "comparison_id": "comparison-1",
            "comparison_evidence_digest": comparison_digest,
            "final_confirmed_by": "user-1",
            "confirmation_token": "confirmation-" + ("x" * 32),
        },
        "acceptance": {
            "artifact_digest": digest,
            "input_digest": input_digest,
            "profile_digest": profile_digest,
            "engine_source_digest": engine_source_digest,
            "engine_build_digest": engine_build_digest,
            "comparison_id": "comparison-1",
            "comparison_evidence_digest": comparison_digest,
            "ready_for_live_checks": True,
            "preflight_verified": True,
            "pair_preflight_verified": True,
            "final_confirmation_required": True,
            "can_upload": False,
            "can_start_print": False,
        },
        "authorization": {
            "outcome": "allow",
            "evaluation_id": "authorization:1",
            "decision_id": "decision:1",
            "effective_action": {"action_type": "artifact.upload"},
        },
        "capability": {
            "capability_id": "artifact.upload",
            "provider_id": "provider:custom",
        },
    }


def prepare(inputs: dict[str, dict]) -> dict:
    return ForgeExecutive().prepare_confirmed_artifact_execution(**inputs)


def test_prepares_non_dispatching_executive_request(inputs: dict[str, dict]) -> None:
    request = prepare(inputs)

    assert request["classification"] == "command"
    assert request["payload"]["final_confirmation_verified"] is True
    assert request["payload"]["physical_dispatch_allowed"] is False
    assert request["payload"]["requires_runtime_dispatcher"] is True
    assert request["payload"]["input_digest"] == "b" * 64
    assert request["payload"]["profile_digest"] == "c" * 64
    assert request["payload"]["engine_source_digest"] == "d" * 64
    assert request["payload"]["engine_build_digest"] == "e" * 64
    assert request["payload"]["comparison_evidence_digest"] == "f" * 64
    assert "confirmation_token" not in request["payload"]


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("job", "state", "final_confirmation_required"),
        ("job", "artifact_digest", "b" * 64),
        ("job", "profile_digest", "d" * 64),
        ("job", "engine_build_digest", "f" * 64),
        ("job", "comparison_evidence_digest", "a" * 64),
        ("acceptance", "can_upload", True),
        ("acceptance", "preflight_verified", False),
        ("acceptance", "pair_preflight_verified", False),
        ("mission", "state", "created"),
    ],
)
def test_rejects_unconfirmed_or_mismatched_inputs(
    inputs: dict[str, dict], section: str, field: str, value: object
) -> None:
    changed = deepcopy(inputs)
    changed[section][field] = value

    with pytest.raises(ExecutiveError):
        prepare(changed)
