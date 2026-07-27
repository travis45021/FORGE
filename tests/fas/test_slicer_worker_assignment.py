"""Tests for binding isolated workers to requests and ephemeral profiles."""

from copy import deepcopy

import pytest

from forge.fas.slicer_worker import (
    REQUIRED_FORBIDDEN,
    SlicerWorkerBoundary,
    SlicerWorkerError,
)


@pytest.fixture
def profile() -> dict:
    return {
        "profile_digest": "b" * 64,
        "lifecycle": "ephemeral",
        "persist_after_worker": False,
        "delete_after_result": True,
        "contains_transport_endpoint": False,
        "contains_credentials": False,
        "cloud_access": False,
        "can_control_printer": False,
        "can_upload": False,
        "can_start_print": False,
    }


@pytest.fixture
def slicer_request() -> dict:
    return {
        "contract_version": "1.0",
        "request_id": "request:production",
        "input": {
            "format": "3mf",
            "digest": "a" * 64,
            "path": "quarantine/part.3mf",
        },
        "context": "production",
        "profile_digest": "b" * 64,
        "profile_ephemeral": True,
        "authority": {
            "mission_id": "mission:1",
            "user_confirmation_stage": "created_mission",
        },
    }


@pytest.fixture
def manifest() -> dict:
    return {
        "worker_id": "worker:production",
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


def test_assigns_single_use_worker_without_authority(
    manifest: dict, slicer_request: dict, profile: dict
) -> None:
    assignment = SlicerWorkerBoundary().assign(manifest, slicer_request, profile)

    assert assignment["single_use"] is True
    assert assignment["profile_delete_after_result"] is True
    assert assignment["can_control_hardware"] is False
    assert assignment["can_upload"] is False
    assert assignment["can_start_print"] is False


@pytest.mark.parametrize(
    ("target", "field", "value", "message"),
    [
        ("manifest", "context", "twin", "contexts"),
        ("profile", "profile_digest", "c" * 64, "digest"),
        ("profile", "can_upload", True, "authority"),
        ("request", "profile_ephemeral", False, "ephemeral"),
    ],
)
def test_rejects_stale_or_authoritative_assignment(
    manifest: dict,
    slicer_request: dict,
    profile: dict,
    target: str,
    field: str,
    value: object,
    message: str,
) -> None:
    values = {
        "manifest": deepcopy(manifest),
        "request": deepcopy(slicer_request),
        "profile": deepcopy(profile),
    }
    values[target][field] = value

    with pytest.raises(SlicerWorkerError, match=message):
        SlicerWorkerBoundary().assign(
            values["manifest"], values["request"], values["profile"]
        )
