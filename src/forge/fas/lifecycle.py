"""FAS-027 reference lifecycle and service-management contract."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any


class LifecycleError(ValueError):
    """Raised when a service lifecycle operation violates its contract."""


def _validate_observed_at(value: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise LifecycleError("observed_at must be a UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise LifecycleError("observed_at must be a valid UTC timestamp") from exc


STATES = {
    "registered",
    "starting",
    "ready",
    "degraded",
    "stopping",
    "stopped",
    "failed",
}
TRANSITIONS = {
    "registered": {"starting", "stopped"},
    "starting": {"ready", "degraded", "failed", "stopping"},
    "ready": {"degraded", "stopping", "failed"},
    "degraded": {"ready", "stopping", "failed"},
    "stopping": {"stopped", "failed"},
    "stopped": {"starting"},
    "failed": {"starting", "stopping", "stopped"},
}


class ServiceLifecycle:
    """Manage local service state without silently acquiring authority.

    This is an in-memory reference contract. A real supervisor may implement
    process spawning, health probes, and persistence while preserving these
    boundaries.
    """

    def __init__(self) -> None:
        self._services: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def register(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(manifest))
        required = {"service_id", "version", "dependencies", "provides", "state"}
        missing = sorted(required - item.keys())
        if missing:
            raise LifecycleError(f"service manifest missing: {', '.join(missing)}")
        if item["state"] != "registered" or item["service_id"] in self._services:
            raise LifecycleError("service identity or initial state is invalid")
        if not isinstance(item["dependencies"], list) or not isinstance(
            item["provides"], list
        ):
            raise LifecycleError("dependencies and provides must be lists")
        if not isinstance(item["service_id"], str) or not item["service_id"]:
            raise LifecycleError("service identity must be a non-empty string")
        for field in ("dependencies", "provides"):
            values = item[field]
            if any(not isinstance(value, str) or not value for value in values):
                raise LifecycleError(f"{field} must contain non-empty strings")
            if len(values) != len(set(values)):
                raise LifecycleError(f"{field} must not contain duplicates")
        if item["service_id"] in item["dependencies"]:
            raise LifecycleError("service cannot depend on itself")
        self._services[item["service_id"]] = item
        self._record("service.registered", item["service_id"], "manifest_registered")
        return deepcopy(item)

    def transition(
        self,
        service_id: str,
        state: str,
        *,
        reason: str,
        authority_reference: str,
        observed_at: str,
        dependencies_ready: bool = True,
        health: str = "unknown",
    ) -> dict[str, Any]:
        service = self._require(service_id)
        if state not in STATES or state not in TRANSITIONS[service["state"]]:
            raise LifecycleError(
                f"invalid service transition: {service['state']} -> {state}"
            )
        if not authority_reference:
            raise LifecycleError("lifecycle transition requires authority reference")
        _validate_observed_at(observed_at)
        if not dependencies_ready and state in {"starting", "ready"}:
            raise LifecycleError("dependencies are not ready")
        if health not in {"unknown", "healthy", "degraded", "failed"}:
            raise LifecycleError("invalid health value")
        service.update(
            {
                "state": state,
                "reason": reason,
                "observed_at": observed_at,
                "health": health,
            }
        )
        self._record("service.state.changed", service_id, reason)
        return deepcopy(service)

    def plan_start(
        self, service_id: str, *, requested_by: str, approval_reference: str
    ) -> dict[str, Any]:
        service = self._require(service_id)
        if not requested_by or not approval_reference:
            raise LifecycleError("start requires explicit user request and approval")
        if service["state"] not in {"registered", "stopped", "failed"}:
            raise LifecycleError("service is not startable")
        return {
            "operation": "start",
            "service_id": service_id,
            "requested_by": requested_by,
            "approval_reference": approval_reference,
            "physical_commands_allowed": False,
        }

    def plan_stop(
        self, service_id: str, *, requested_by: str, approval_reference: str
    ) -> dict[str, Any]:
        service = self._require(service_id)
        if not requested_by or not approval_reference:
            raise LifecycleError("stop requires explicit user request and approval")
        if service["state"] in {"registered", "stopped"}:
            raise LifecycleError("service is already stopped")
        return {
            "operation": "stop",
            "service_id": service_id,
            "requested_by": requested_by,
            "approval_reference": approval_reference,
            "physical_commands_allowed": False,
        }

    def service(self, service_id: str) -> dict[str, Any]:
        return deepcopy(self._require(service_id))

    def services(self) -> list[dict[str, Any]]:
        return [deepcopy(item) for item in self._services.values()]

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def _require(self, service_id: str) -> dict[str, Any]:
        try:
            return self._services[service_id]
        except KeyError as exc:
            raise LifecycleError(f"unknown service: {service_id}") from exc

    def _record(self, event_type: str, service_id: str, reason: str) -> None:
        self._history.append(
            {"event_type": event_type, "service_id": service_id, "reason": reason}
        )
