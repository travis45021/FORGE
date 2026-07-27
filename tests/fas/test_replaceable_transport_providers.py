"""Tests that printer transports remain capability-based and replaceable."""

import pytest

from forge.fas.transport import (
    HardwareTransportRegistry,
    TransportError,
    capability_provider_manifest,
    moonraker_klipper_reference_manifest,
)


def test_moonraker_is_a_reference_not_a_compatibility_boundary() -> None:
    manifest = moonraker_klipper_reference_manifest()

    assert manifest["tested_reference"] == "moonraker-klipper"
    assert manifest["compatibility_boundary"] is False
    assert manifest["direct_slicer_control"] is False
    assert manifest["requires_runtime_dispatcher"] is True


def test_custom_provider_can_offer_same_upload_capability() -> None:
    registry = HardwareTransportRegistry()
    moonraker = moonraker_klipper_reference_manifest()
    custom = capability_provider_manifest(
        provider_id="provider:user-built-printer",
        transport="user-local-bridge",
        capabilities=["artifact.upload"],
    )

    registry.register(moonraker)
    registry.register(custom)

    assert [item["provider_id"] for item in registry.discover()] == [
        "provider:moonraker-local",
        "provider:user-built-printer",
    ]


@pytest.mark.parametrize("endpoint_scope", ["internet", "cloud"])
def test_v1_provider_factory_rejects_nonlocal_scope(endpoint_scope: str) -> None:
    with pytest.raises(TransportError):
        capability_provider_manifest(
            provider_id="provider:remote",
            transport="remote-api",
            capabilities=["artifact.upload"],
            endpoint_scope=endpoint_scope,
        )
