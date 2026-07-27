"""Fault-injection tests for fail-closed slicer worker supervision."""

import pytest

from forge.fas.slicer_worker import (
    REQUIRED_FORBIDDEN,
    SlicerWorkerSupervisor,
)


@pytest.fixture
def manifest() -> dict:
    return {
        "worker_id": "worker-production",
        "context": "production",
        "workspace": {
            "input": "work/production/input",
            "output": "work/production/output",
            "logs": "work/production/logs",
        },
        "limits": {
            "timeout_seconds": 300,
            "memory_bytes": 1_000_000,
            "disk_bytes": 10_000_000,
        },
        "forbidden_capabilities": sorted(REQUIRED_FORBIDDEN),
    }


def assess(manifest: dict, **changes: object) -> dict:
    arguments = {
        "outcome": "completed",
        "context_id": "context:current",
        "current_context_id": "context:current",
        "peak_memory_bytes": 500_000,
        "disk_written_bytes": 5_000_000,
        "artifact_digest": "a" * 64,
        **changes,
    }
    return SlicerWorkerSupervisor().assess_outcome(manifest, **arguments)


def test_completed_worker_still_has_no_physical_authority(manifest: dict) -> None:
    result = assess(manifest)

    assert result["status"] == "succeeded"
    assert result["artifact_accepted"] is True
    assert result["can_upload"] is False
    assert result["can_start_print"] is False
    assert result["worker_reuse_allowed"] is False


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"outcome": "crashed"}, "worker_crashed"),
        ({"outcome": "timed_out"}, "worker_timed_out"),
        ({"outcome": "cancelled"}, "worker_cancelled"),
        ({"peak_memory_bytes": 1_000_001}, "memory_limit_exceeded"),
        ({"disk_written_bytes": 10_000_001}, "disk_limit_exceeded"),
        ({"current_context_id": "context:new"}, "stale_execution_context"),
    ],
)
def test_worker_faults_fail_closed(manifest: dict, changes: dict, reason: str) -> None:
    result = assess(manifest, **changes)

    assert result["status"] == "failed_closed"
    assert result["reason"] == reason
    assert result["artifact_digest"] is None
    assert result["artifact_accepted"] is False
    assert result["retry_requires_fresh_context"] is True
    assert result["workspace_cleanup_required"] is True
    assert result["can_upload"] is False
    assert result["can_start_print"] is False
