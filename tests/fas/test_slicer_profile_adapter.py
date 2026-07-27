"""Tests for ephemeral, hardware-neutral slicer worker profiles."""

from copy import deepcopy

import pytest

from forge.fas.slicer_profile import SlicerProfileAdapter, SlicerProfileError


@pytest.fixture
def machine() -> dict:
    return {
        "object_id": "machine:user-built",
        "version": 3,
        "lifecycle_state": "active",
        "knowledge_state": "locally_measured",
        "health": {"state": "healthy"},
        "capabilities": ["fff.extrusion", "heated_bed"],
        "limits": {"maximum_nozzle_temperature_c": 300},
        "unknown_fields": [],
        "evidence_refs": ["evidence:measurement-1"],
    }


@pytest.fixture
def configuration() -> dict:
    return {
        "profile_ids": ["profile:safe", "profile:material"],
        "values": {"layer_height_mm": 0.2, "nozzle_temperature_c": 210},
        "hard_limits": {"maximum_nozzle_temperature_c": 300},
    }


@pytest.fixture
def intent() -> dict:
    return {
        "intent_id": "intent:1",
        "source_digest": "a" * 64,
        "printer_capabilities": ["fff.extrusion"],
        "material": {"name": "PLA"},
        "process": {"profile_digest": "b" * 64},
        "user_decisions": {
            "context_confirmed": True,
            "mission_reviewed": True,
        },
    }


def test_derives_deterministic_ephemeral_profile_for_custom_hardware(
    machine: dict, configuration: dict, intent: dict
) -> None:
    adapter = SlicerProfileAdapter()
    first = adapter.derive(machine=machine, configuration=configuration, intent=intent)
    second = adapter.derive(
        machine=deepcopy(machine),
        configuration=deepcopy(configuration),
        intent=deepcopy(intent),
    )

    assert first["profile_digest"] == second["profile_digest"]
    assert first["hardware_neutral"] is True
    assert first["lifecycle"] == "ephemeral"
    assert first["persist_after_worker"] is False
    assert first["can_control_printer"] is False
    assert first["can_upload"] is False


def test_rejects_unresolved_machine_unknowns(
    machine: dict, configuration: dict, intent: dict
) -> None:
    machine["unknown_fields"] = ["nozzle_diameter"]

    with pytest.raises(SlicerProfileError, match="unknowns"):
        SlicerProfileAdapter().derive(
            machine=machine, configuration=configuration, intent=intent
        )


def test_rejects_printer_endpoint_or_credentials(
    machine: dict, configuration: dict, intent: dict
) -> None:
    configuration["values"]["endpoint"] = "http://printer.local"

    with pytest.raises(SlicerProfileError, match="forbidden fields"):
        SlicerProfileAdapter().derive(
            machine=machine, configuration=configuration, intent=intent
        )


def test_rejects_capability_mismatch(
    machine: dict, configuration: dict, intent: dict
) -> None:
    intent["printer_capabilities"].append("laser.cutting")

    with pytest.raises(SlicerProfileError, match="does not satisfy"):
        SlicerProfileAdapter().derive(
            machine=machine, configuration=configuration, intent=intent
        )
