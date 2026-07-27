"""Capability-bound plugin manifest registry for canonical FAS-014."""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .capabilities import CapabilityRegistry


class PluginError(ValueError):
    """Raised when a plugin violates FAS-014."""


PLUGIN_TYPES = {
    "capability_provider",
    "transport",
    "ai_provider",
    "mission",
    "profile",
    "interface",
    "knowledge",
}
TRUST_STATES = {
    "unverified",
    "provisional",
    "locally_trusted",
    "validated",
    "verified_publisher",
    "official_forge",
    "quarantined",
    "blocked",
}
SENSITIVE_PERMISSIONS = {
    "network.internet",
    "machine.motion.control",
    "machine.thermal.control",
    "firmware.flash",
    "policy.modify",
}
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9_]+){2,}$")


class PluginRegistry:
    """Validates plugins without treating installation as trust or authority."""

    def __init__(self, capabilities: CapabilityRegistry | None = None) -> None:
        self._capabilities = capabilities or CapabilityRegistry()
        self._plugins: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def discover(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(manifest))
        self._validate_manifest(item)
        plugin_id = item["plugin_id"]
        if plugin_id in self._plugins:
            raise PluginError("plugin identifiers are immutable per version")
        record = {
            "manifest": item,
            "state": "manifest_validated",
            "trust_state": "unverified",
            "granted_permissions": [],
            "explanation": "Manifest valid; permissions and capabilities not active.",
        }
        self._plugins[plugin_id] = record
        self._record("plugin.manifest.validated", plugin_id)
        return deepcopy(record)

    def validate(
        self,
        plugin_id: str,
        *,
        granted_permissions: list[str],
        passed_contract_tests: list[str],
        trust_state: str = "provisional",
    ) -> dict[str, Any]:
        record = self._require(plugin_id)
        manifest = record["manifest"]
        if trust_state not in TRUST_STATES or trust_state in {
            "quarantined",
            "blocked",
        }:
            raise PluginError("invalid activation trust state")
        requested = set(manifest["permissions"])
        granted = set(granted_permissions)
        if not granted <= requested:
            raise PluginError("plugin cannot receive undeclared permissions")
        required_tests = set(manifest["validation_tests"])
        if not required_tests <= set(passed_contract_tests):
            record["state"] = "validation_failed"
            record["explanation"] = "Declared contract tests have not all passed."
            self._record("plugin.validation.failed", plugin_id)
            return deepcopy(record)
        missing = requested - granted
        if missing:
            record["state"] = "configured"
            record["explanation"] = (
                "Not ready; requested permissions remain ungranted: "
                + ", ".join(sorted(missing))
            )
            return deepcopy(record)
        record.update(
            {
                "state": "ready",
                "trust_state": trust_state,
                "granted_permissions": sorted(granted),
                "explanation": "Contracts passed and declared permissions granted.",
            }
        )
        self._record("plugin.ready", plugin_id)
        return deepcopy(record)

    def activate(self, plugin_id: str, *, executive_authorized: bool) -> dict[str, Any]:
        record = self._require(plugin_id)
        if record["state"] != "ready":
            raise PluginError("plugin must be ready before activation")
        if executive_authorized is not True:
            raise PluginError("plugin activation requires Executive authorization")
        manifest = record["manifest"]
        if manifest["experimental"] and manifest["execution_mode"] == "normal":
            raise PluginError("experimental plugins require an active testing gate")
        for capability in manifest["capabilities"]:
            permission = capability["required_permission"]
            if permission not in record["granted_permissions"]:
                raise PluginError("capability lacks its declared permission")
            contract = {
                "capability_id": capability["capability_id"],
                "version": capability["version"],
                "provider_id": capability["provider_id"],
                "operations": deepcopy(capability["operations"]),
                "limitations": deepcopy(capability["limitations"]),
                "plugin_id": plugin_id,
            }
            self._capabilities.register(
                contract,
                healthy=True,
                trusted=record["trust_state"]
                in {
                    "locally_trusted",
                    "validated",
                    "verified_publisher",
                    "official_forge",
                },
            )
        record["state"] = "active"
        record["explanation"] = "Active within declared permissions and capabilities."
        self._record("plugin.activated", plugin_id)
        return deepcopy(record)

    def quarantine(self, plugin_id: str, *, reason: str) -> dict[str, Any]:
        record = self._require(plugin_id)
        if len(reason.strip()) < 3:
            raise PluginError("quarantine reason is required")
        record.update(
            {
                "state": "quarantined",
                "trust_state": "quarantined",
                "explanation": reason.strip(),
            }
        )
        self._record("plugin.quarantined", plugin_id)
        return deepcopy(record)

    def plugin(self, plugin_id: str) -> dict[str, Any] | None:
        record = self._plugins.get(plugin_id)
        return deepcopy(record) if record else None

    def capabilities(self) -> CapabilityRegistry:
        return self._capabilities

    def history(self) -> list[dict[str, str]]:
        return deepcopy(self._history)

    def _validate_manifest(self, item: Mapping[str, Any]) -> None:
        required = {
            "schema_version",
            "plugin_id",
            "name",
            "version",
            "api_version",
            "plugin_type",
            "publisher",
            "description",
            "fas_compliance",
            "capabilities",
            "permissions",
            "services",
            "isolation",
            "network_scope",
            "configuration_schema",
            "validation_tests",
            "experimental",
            "execution_mode",
            "limitations",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise PluginError(f"manifest missing fields: {', '.join(missing)}")
        if not _PLUGIN_ID.fullmatch(item["plugin_id"]):
            raise PluginError("plugin identifier must use a publisher namespace")
        if item["plugin_id"].startswith("forge.official."):
            raise PluginError("official namespace requires separate publisher trust")
        if not _SEMVER.fullmatch(item["version"]):
            raise PluginError("plugin version must be semantic")
        if item["plugin_type"] not in PLUGIN_TYPES:
            raise PluginError("unknown plugin type")
        for field in ("permissions", "services", "validation_tests", "limitations"):
            if not isinstance(item[field], list) or len(item[field]) != len(
                set(item[field])
            ):
                raise PluginError(f"{field} must be a unique list")
        if item["isolation"] not in {"separate_process", "in_process_reduced"}:
            raise PluginError("unsupported isolation mode")
        if item["network_scope"] not in {"none", "local_only", "internet"}:
            raise PluginError("unsupported network scope")
        if (
            item["network_scope"] == "internet"
            and "network.internet" not in item["permissions"]
        ):
            raise PluginError("internet scope requires explicit permission")
        if item["experimental"] and item["execution_mode"] not in {
            "simulation_only",
            "test_hardware",
        }:
            raise PluginError("experimental plugins require a testing gate")
        for capability in item["capabilities"]:
            fields = {
                "capability_id",
                "version",
                "provider_id",
                "operations",
                "limitations",
                "required_permission",
            }
            if fields - capability.keys():
                raise PluginError("capability declaration is incomplete")
            if capability["required_permission"] not in item["permissions"]:
                raise PluginError("capability permission must be declared")

    def _require(self, plugin_id: str) -> dict[str, Any]:
        try:
            return self._plugins[plugin_id]
        except KeyError as exc:
            raise PluginError(f"unknown plugin: {plugin_id}") from exc

    def _record(self, event_type: str, plugin_id: str) -> None:
        self._history.append({"event_type": event_type, "plugin_id": plugin_id})


def custom_component_manifest(
    *,
    plugin_id: str,
    name: str,
    category: str,
    capability_id: str,
    operations: list[str],
    limits: Mapping[str, Any],
    connection: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a least-privilege provisional no-code component manifest."""
    if not operations:
        raise PluginError("custom component requires declared operations")
    permission = f"machine.{category}.control"
    return {
        "schema_version": "1.0.0",
        "plugin_id": plugin_id,
        "name": name,
        "version": "0.1.0",
        "api_version": ">=1.0.0 <2.0.0",
        "plugin_type": "capability_provider",
        "publisher": "local-user",
        "description": f"Local custom {category} component.",
        "fas_compliance": ["FAS-003", "FAS-010", "FAS-014", "FAS-018"],
        "capabilities": [
            {
                "capability_id": capability_id,
                "version": "1.0.0",
                "provider_id": f"{plugin_id}.provider",
                "operations": [{"name": value} for value in operations],
                "limitations": [
                    "provisional_custom_hardware",
                    f"limits:{dict(limits)}",
                ],
                "required_permission": permission,
            }
        ],
        "permissions": [permission],
        "services": ["events", "logging", "capability_registry"],
        "isolation": "separate_process",
        "network_scope": "none",
        "configuration_schema": {
            "connection": dict(connection),
            "limits": dict(limits),
        },
        "validation_tests": ["manifest", "configuration", "capability_contract"],
        "experimental": True,
        "execution_mode": "test_hardware",
        "limitations": ["provisional", "unknown_functions_unavailable"],
    }
