"""Tests for one-engine production/twin worker pair assignments."""

from copy import deepcopy

import pytest

from forge.fas.slicer_worker import (
    REQUIRED_FORBIDDEN,
    SlicerWorkerBoundary,
    SlicerWorkerError,
)


def manifest(context: str) -> dict:
    return {
        "worker_id": f"worker:{context}",
        "context": context,
        "workspace": {
            "input": f"work/{context}/input",
            "output": f"work/{context}/output",
            "logs": f"work/{context}/logs",
        },
        "limits": {
            "timeout_seconds": 300,
            "memory_bytes": 1_000_000,
            "disk_bytes": 10_000_000,
        },
        "forbidden_capabilities": sorted(REQUIRED_FORBIDDEN),
    }


def request(context: str) -> dict:
    return {
        "contract_version": "1.0",
        "request_id": f"request:{context}",
        "input": {
            "format": "3mf",
            "digest": "a" * 64,
            "path": f"work/{context}/input/part.3mf",
        },
        "context": context,
        "profile_digest": "b" * 64,
        "profile_ephemeral": True,
        "authority": {
            "mission_id": "mission:1",
            "user_confirmation_stage": "created_mission",
        },
    }


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


def engine() -> dict:
    return {
        "name": "reviewed-engine",
        "version": "pinned",
        "source_digest": "c" * 64,
        "build_digest": "d" * 64,
    }


def assign_pair(**changes: object) -> dict:
    values = {
        "production_manifest": manifest("production"),
        "twin_manifest": manifest("twin"),
        "production_request": request("production"),
        "twin_request": request("twin"),
        "profile": profile(),
        "engine": engine(),
        **changes,
    }
    return SlicerWorkerBoundary().assign_pair(**values)


def test_pair_uses_one_engine_input_and_profile_with_isolated_workspaces() -> None:
    assignment = assign_pair()

    assert assignment["same_engine_build"] is True
    assert assignment["same_input"] is True
    assert assignment["same_profile"] is True
    assert assignment["workspaces_isolated"] is True
    assert assignment["production"]["workspace"] != assignment["twin"]["workspace"]
    assert assignment["can_control_hardware"] is False


def test_rejects_different_input_digest() -> None:
    twin_request = request("twin")
    twin_request["input"]["digest"] = "e" * 64

    with pytest.raises(SlicerWorkerError, match="input digests"):
        assign_pair(twin_request=twin_request)


def test_rejects_different_profile_digest() -> None:
    twin_request = request("twin")
    twin_request["profile_digest"] = "e" * 64

    with pytest.raises(SlicerWorkerError, match="profile digest"):
        assign_pair(twin_request=twin_request)


def test_rejects_invalid_engine_build_provenance() -> None:
    changed_engine = deepcopy(engine())
    changed_engine["build_digest"] = "not-a-digest"

    with pytest.raises(SlicerWorkerError, match="build_digest"):
        assign_pair(engine=changed_engine)
