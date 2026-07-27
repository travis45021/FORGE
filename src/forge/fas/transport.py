"""FAS-028 capability-first hardware transport boundary."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class TransportError(ValueError):
    """Raised when a hardware provider contract is invalid or unsafe."""


def capability_provider_manifest(
    *,
    provider_id: str,
    transport: str,
    capabilities: list[str],
    endpoint_scope: str = "local_only",
    tested_reference: str | None = None,
) -> dict[str, Any]:
    """Create a replaceable, hardware-neutral transport provider manifest."""
    if not provider_id.startswith("provider:"):
        raise TransportError("provider identity must use the provider namespace")
    if not transport.strip():
        raise TransportError("provider transport is required")
    if (
        not capabilities
        or any(not capability.strip() for capability in capabilities)
        or len(capabilities) != len(set(capabilities))
    ):
        raise TransportError("provider capabilities must be unique and non-empty")
    if endpoint_scope not in {"offline", "local_only"}:
        raise TransportError("v1 hardware providers must remain offline or local-only")
    return {
        "schema_version": "1.0.0",
        "provider_id": provider_id,
        "transport": transport,
        "capabilities": sorted(capabilities),
        "state": "registered",
        "health": "unknown",
        "endpoint_scope": endpoint_scope,
        "tested_reference": tested_reference,
        "compatibility_boundary": False,
        "direct_slicer_control": False,
        "requires_runtime_dispatcher": True,
    }


def moonraker_klipper_reference_manifest(
    *, provider_id: str = "provider:moonraker-local"
) -> dict[str, Any]:
    """Describe Moonraker/Klipper as one tested local reference provider."""
    return capability_provider_manifest(
        provider_id=provider_id,
        transport="moonraker-http-local",
        capabilities=[
            "artifact.upload",
            "job.start",
            "job.status",
            "job.cancel",
        ],
        endpoint_scope="local_only",
        tested_reference="moonraker-klipper",
    )


class HardwareTransportRegistry:
    """Discover providers and prepare bounded commands without sending them."""

    def __init__(self) -> None:
        self._providers: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def register(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(manifest))
        required = {"provider_id", "transport", "capabilities", "state", "health"}
        missing = sorted(required - item.keys())
        if missing:
            raise TransportError(f"provider manifest missing: {', '.join(missing)}")
        if item["provider_id"] in self._providers or item["state"] != "registered":
            raise TransportError("provider identity or initial state is invalid")
        if item["health"] not in {"unknown", "healthy", "degraded", "failed"}:
            raise TransportError("invalid provider health")
        if not isinstance(item["capabilities"], list) or not item["capabilities"]:
            raise TransportError("provider capabilities must be a non-empty list")
        self._providers[item["provider_id"]] = item
        self._record("provider.registered", item["provider_id"])
        return deepcopy(item)

    def set_health(
        self, provider_id: str, health: str, *, observed_at: str
    ) -> dict[str, Any]:
        provider = self._require(provider_id)
        if health not in {"unknown", "healthy", "degraded", "failed"}:
            raise TransportError("invalid provider health")
        provider.update({"health": health, "observed_at": observed_at})
        self._record("provider.health.changed", provider_id)
        return deepcopy(provider)

    def discover(self) -> list[dict[str, Any]]:
        return [deepcopy(self._providers[key]) for key in sorted(self._providers)]

    def prepare_command(
        self,
        provider_id: str,
        command: Mapping[str, Any],
        *,
        authorization_verified: bool,
        verification_passed: bool,
        runtime_lease_active: bool,
        user_confirmation: bool,
    ) -> dict[str, Any]:
        provider = self._require(provider_id)
        item = deepcopy(dict(command))
        required = {
            "command_id",
            "capability_id",
            "operation",
            "parameters",
            "expires_at",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise TransportError(f"command missing: {', '.join(missing)}")
        if item.get("raw_hardware_command") is not None:
            raise TransportError("raw hardware commands are not accepted")
        if provider["health"] != "healthy":
            raise TransportError("provider is not healthy")
        if item["capability_id"] not in provider["capabilities"]:
            raise TransportError("provider does not offer requested capability")
        if not all(
            (
                authorization_verified,
                verification_passed,
                runtime_lease_active,
                user_confirmation,
            )
        ):
            raise TransportError(
                "authorization, verification, lease, and user confirmation are all required"
            )
        prepared = {
            "provider_id": provider_id,
            "command": item,
            "physical_dispatch_allowed": False,
            "requires_runtime_dispatcher": True,
            "requires_fresh_user_confirmation": True,
        }
        self._record("provider.command.prepared", provider_id)
        return prepared

    def prepare_artifact_upload(
        self,
        provider_id: str,
        job: Mapping[str, Any],
        *,
        runtime_lease_active: bool,
        authorization_verified: bool,
    ) -> dict[str, Any]:
        """Prepare an artifact handoff only after the evidence-backed fourth click."""
        provider = self._require(provider_id)
        item = deepcopy(dict(job))
        if provider["health"] != "healthy":
            raise TransportError("provider is not healthy")
        if "artifact.upload" not in provider["capabilities"]:
            raise TransportError("provider does not offer controlled artifact upload")
        if item.get("provider_id") != provider_id:
            raise TransportError("job provider does not match upload provider")
        if item.get("state") != "upload_pending":
            raise TransportError("job must pass final confirmation before upload")
        if item.get("click_count") != 3 or not item.get("final_confirmed_by"):
            raise TransportError("evidence-backed fourth click is required")
        if item.get("artifact_preflight_verified") is not True:
            raise TransportError("deterministic artifact preflight is required")
        if item.get("artifact_pair_preflight_verified") is not True:
            raise TransportError("coordinated pair preflight is required")
        confirmation_token = item.get("confirmation_token")
        if not isinstance(confirmation_token, str) or len(confirmation_token) < 32:
            raise TransportError("fresh final-confirmation token is required")
        artifact_digest = item.get("artifact_digest")
        if (
            not isinstance(artifact_digest, str)
            or len(artifact_digest) != 64
            or any(character not in "0123456789abcdef" for character in artifact_digest)
        ):
            raise TransportError("job artifact digest must be lowercase SHA-256")
        for field in (
            "input_digest",
            "profile_digest",
            "engine_source_digest",
            "engine_build_digest",
        ):
            value = item.get(field)
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise TransportError(
                    f"job {field.replace('_', ' ')} must be lowercase SHA-256"
                )
        if not runtime_lease_active or not authorization_verified:
            raise TransportError("active runtime lease and authorization are required")
        prepared = {
            "provider_id": provider_id,
            "job_id": item["job_id"],
            "artifact_digest": artifact_digest,
            "input_digest": item["input_digest"],
            "profile_digest": item["profile_digest"],
            "engine_source_digest": item["engine_source_digest"],
            "engine_build_digest": item["engine_build_digest"],
            "confirmed_by": item["final_confirmed_by"],
            "confirmation_token": confirmation_token,
            "artifact_preflight_verified": True,
            "artifact_pair_preflight_verified": True,
            "historical_replay_allowed": False,
            "physical_dispatch_allowed": False,
            "requires_runtime_dispatcher": True,
            "fourth_click_satisfied": True,
        }
        self._record("provider.artifact_upload.prepared", provider_id)
        return prepared

    def provider(self, provider_id: str) -> dict[str, Any]:
        return deepcopy(self._require(provider_id))

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def _require(self, provider_id: str) -> dict[str, Any]:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise TransportError(f"unknown provider: {provider_id}") from exc

    def _record(self, event_type: str, provider_id: str) -> None:
        self._history.append({"event_type": event_type, "provider_id": provider_id})
