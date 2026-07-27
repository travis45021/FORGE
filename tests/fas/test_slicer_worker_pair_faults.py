"""Tests for coordinated fail-closed production/twin outcomes."""

from copy import deepcopy

import pytest

from forge.fas.slicer_worker import SlicerWorkerError, SlicerWorkerSupervisor


def worker_assignment(context: str) -> dict:
    return {
        "worker_id": f"worker:{context}",
        "request_id": f"request:{context}",
        "context": context,
        "profile_digest": "b" * 64,
        "workspace": {
            "input": f"work/{context}/input",
            "output": f"work/{context}/output",
            "logs": f"work/{context}/logs",
        },
        "limits": {},
        "single_use": True,
        "profile_delete_after_result": True,
        "can_control_hardware": False,
        "can_upload": False,
        "can_start_print": False,
    }


def pair_assignment() -> dict:
    return {
        "engine": {
            "name": "reviewed-engine",
            "version": "pinned",
            "source_digest": "c" * 64,
            "build_digest": "d" * 64,
        },
        "input_digest": "a" * 64,
        "profile_digest": "b" * 64,
        "production": worker_assignment("production"),
        "twin": worker_assignment("twin"),
        "workspaces_isolated": True,
        "same_engine_build": True,
        "same_input": True,
        "same_profile": True,
        "can_control_hardware": False,
        "can_upload": False,
        "can_start_print": False,
    }


def outcome(context: str, *, succeeded: bool = True) -> dict:
    return {
        "schema_version": "1.0.0",
        "worker_id": f"worker:{context}",
        "context": context,
        "context_id": f"context:{context}",
        "status": "succeeded" if succeeded else "failed_closed",
        "reason": "worker_completed" if succeeded else "worker_crashed",
        "artifact_digest": ("e" * 64) if succeeded else None,
        "artifact_accepted": succeeded,
        "workspace_cleanup_required": True,
        "worker_reuse_allowed": False,
        "retry_requires_fresh_context": not succeeded,
        "can_upload": False,
        "can_start_print": False,
        "can_control_hardware": False,
    }


def assess(production: dict, twin: dict, assignment: dict | None = None) -> dict:
    return SlicerWorkerSupervisor().assess_pair(
        assignment or pair_assignment(),
        production=production,
        twin=twin,
    )


def test_successful_pair_is_ready_only_for_preflight() -> None:
    result = assess(outcome("production"), outcome("twin"))

    assert result["status"] == "ready_for_preflight"
    assert result["artifacts_eligible_for_preflight"] is True
    assert result["can_compare"] is True
    assert result["can_upload"] is False
    assert result["can_start_print"] is False


@pytest.mark.parametrize("failed_context", ["production", "twin"])
def test_one_worker_failure_fails_pair_and_cancels_sibling(
    failed_context: str,
) -> None:
    result = assess(
        outcome("production", succeeded=failed_context != "production"),
        outcome("twin", succeeded=failed_context != "twin"),
    )

    assert result["status"] == "failed_closed"
    assert result["cancel_remaining_worker"] is True
    assert result["artifacts_eligible_for_preflight"] is False
    assert result["retry_requires_fresh_pair"] is True
    assert result["can_compare"] is False


def test_rejects_outcome_from_unassigned_worker() -> None:
    production = outcome("production")
    production["worker_id"] = "worker:other"

    with pytest.raises(SlicerWorkerError, match="production worker outcome"):
        assess(production, outcome("twin"))


def test_rejects_pair_assignment_that_claims_authority() -> None:
    assignment = deepcopy(pair_assignment())
    assignment["can_upload"] = True

    with pytest.raises(SlicerWorkerError, match="not trusted"):
        assess(outcome("production"), outcome("twin"), assignment)


def test_rejects_extra_or_secret_outcome_fields() -> None:
    production = outcome("production")
    production["confirmation_token"] = "must-not-survive"

    with pytest.raises(SlicerWorkerError, match="fields"):
        assess(production, outcome("twin"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reason", "worker_crashed"),
        ("artifact_accepted", False),
        ("retry_requires_fresh_context", True),
        ("workspace_cleanup_required", False),
        ("worker_reuse_allowed", True),
    ],
)
def test_rejects_inconsistent_success_outcome(field: str, value: object) -> None:
    production = outcome("production")
    production[field] = value

    with pytest.raises(SlicerWorkerError, match="outcome"):
        assess(production, outcome("twin"))
