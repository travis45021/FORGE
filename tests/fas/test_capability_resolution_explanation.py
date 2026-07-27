"""Tests for plain-language, hardware-neutral capability explanations."""

from copy import deepcopy

import pytest

from forge.fas.capabilities import CapabilityError, CapabilityRegistry


def contract() -> dict:
    return {
        "capability_id": "artifact.upload",
        "version": "1.2.0",
        "provider_id": "provider:user-built",
        "operations": [{"name": "upload_verified_artifact"}],
    }


def requirement() -> dict:
    return {
        "capability_id": "artifact.upload",
        "version_constraint": "^1.0.0",
        "operations": ["upload_verified_artifact"],
    }


def test_custom_provider_is_explained_without_brand_allowlist() -> None:
    registry = CapabilityRegistry()
    registry.register(contract())

    result = registry.explain_resolution(requirement())

    assert result["available"] is True
    assert result["selected_provider_id"] == "provider:user-built"
    assert result["brand_allowlist_required"] is False
    assert result["custom_hardware_supported"] is True
    assert result["can_execute"] is False


def test_missing_provider_has_plain_language_builder_next_step() -> None:
    result = CapabilityRegistry().explain_resolution(requirement())

    assert result["available"] is False
    assert result["reason_codes"] == ["provider_not_found"]
    assert "Add or build a local provider" in result["next_steps"][0]
    assert result["plain_language"] is True


def test_unhealthy_provider_is_distinguished_from_incompatibility() -> None:
    registry = CapabilityRegistry()
    registry.register(contract(), healthy=False)

    result = registry.explain_resolution(requirement())

    assert result["available"] is False
    assert result["reason_codes"] == ["provider_unhealthy"]
    assert "health" in result["next_steps"][0]


def test_version_and_operation_mismatches_remain_visible() -> None:
    registry = CapabilityRegistry()
    candidate = deepcopy(contract())
    candidate["version"] = "2.0.0"
    candidate["operations"] = [{"name": "inspect_status"}]
    registry.register(candidate)

    result = registry.explain_resolution(requirement())

    assert result["available"] is False
    assert result["reason_codes"] == [
        "operations_missing",
        "version_incompatible",
    ]
    provider = result["considered_providers"][0]
    assert provider["missing_operations"] == ["upload_verified_artifact"]
    assert len(result["next_steps"]) == 2


def test_untrusted_provider_requires_visible_trust_review() -> None:
    registry = CapabilityRegistry()
    registry.register(contract(), trusted=False)

    result = registry.explain_resolution(requirement())

    assert result["reason_codes"] == ["provider_not_trusted"]
    assert "trust evidence" in result["next_steps"][0]


@pytest.mark.parametrize("operations", ["upload", [], [""], [1]])
def test_invalid_operation_requirements_are_rejected(operations: object) -> None:
    invalid = requirement()
    invalid["operations"] = operations

    with pytest.raises(CapabilityError, match="operations"):
        CapabilityRegistry().explain_resolution(invalid)


def test_considered_providers_are_deterministic() -> None:
    registry = CapabilityRegistry()
    newer = contract()
    newer["version"] = "1.3.0"
    newer["provider_id"] = "provider:z"
    older = contract()
    older["provider_id"] = "provider:a"
    registry.register(older, healthy=False)
    registry.register(newer, healthy=False)

    result = registry.explain_resolution(requirement())

    assert [provider["provider_id"] for provider in result["considered_providers"]] == [
        "provider:z",
        "provider:a",
    ]
