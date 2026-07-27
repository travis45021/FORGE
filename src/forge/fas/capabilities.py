"""Deterministic FAS-003 capability registry."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


class CapabilityError(ValueError):
    """Raised for invalid contracts or unresolved requirements."""


_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)")


def _version(value: str) -> tuple[int, int, int]:
    match = _VERSION.match(value)
    if not match:
        raise CapabilityError(f"invalid semantic version: {value}")
    return tuple(int(part) for part in match.groups())


def _compatible(version: str, constraint: str) -> bool:
    actual = _version(version)
    if constraint.startswith("^"):
        wanted = _version(constraint[1:])
        return actual[0] == wanted[0] and actual >= wanted
    if constraint.startswith(">="):
        return actual >= _version(constraint[2:])
    return actual == _version(constraint)


@dataclass(frozen=True)
class RegisteredCapability:
    contract: dict[str, Any]
    healthy: bool
    trusted: bool


class CapabilityRegistry:
    """Register and resolve providers without a hardware allowlist."""

    def __init__(self) -> None:
        self._items: list[RegisteredCapability] = []

    def register(
        self, contract: Mapping[str, Any], *, healthy: bool = True, trusted: bool = True
    ) -> None:
        item = deepcopy(dict(contract))
        required = {"capability_id", "version", "provider_id", "operations"}
        missing = sorted(required - item.keys())
        if missing:
            raise CapabilityError(f"contract missing: {', '.join(missing)}")
        _version(str(item["version"]))
        names = [operation.get("name") for operation in item["operations"]]
        if (
            not names
            or any(not name for name in names)
            or len(names) != len(set(names))
        ):
            raise CapabilityError("operations must have unique names")
        key = (item["capability_id"], item["version"], item["provider_id"])
        if any(
            (
                entry.contract["capability_id"],
                entry.contract["version"],
                entry.contract["provider_id"],
            )
            == key
            for entry in self._items
        ):
            raise CapabilityError("capability provider already registered")
        self._items.append(RegisteredCapability(item, healthy, trusted))

    def resolve(self, requirement: Mapping[str, Any]) -> dict[str, Any]:
        wanted = str(requirement["capability_id"])
        constraint = str(requirement["version_constraint"])
        operations = set(requirement["operations"])
        candidates = []
        for entry in self._items:
            contract = entry.contract
            offered = {operation["name"] for operation in contract["operations"]}
            if (
                entry.healthy
                and entry.trusted
                and contract["capability_id"] == wanted
                and _compatible(contract["version"], constraint)
                and operations <= offered
            ):
                candidates.append(entry)
        if not candidates:
            raise CapabilityError(f"unresolved capability: {wanted} {constraint}")
        candidates.sort(
            key=lambda entry: (
                _version(entry.contract["version"]),
                entry.contract["provider_id"],
            ),
            reverse=True,
        )
        return deepcopy(candidates[0].contract)

    def explain_resolution(self, requirement: Mapping[str, Any]) -> dict[str, Any]:
        """Explain availability without requiring a brand or granting authority."""
        required = {"capability_id", "version_constraint", "operations"}
        missing = sorted(required - requirement.keys())
        if missing:
            raise CapabilityError(f"requirement missing: {', '.join(missing)}")
        wanted = str(requirement["capability_id"])
        constraint = str(requirement["version_constraint"])
        raw_operations = requirement["operations"]
        if not isinstance(raw_operations, list) or any(
            not isinstance(operation, str) or not operation
            for operation in raw_operations
        ):
            raise CapabilityError("operations must be a non-empty list of names")
        operations = set(raw_operations)
        if (
            not wanted
            or not operations
            or any(not operation for operation in operations)
        ):
            raise CapabilityError(
                "capability identity and required operations are required"
            )
        version_text = constraint
        if constraint.startswith("^"):
            version_text = constraint[1:]
        elif constraint.startswith(">="):
            version_text = constraint[2:]
        _version(version_text)

        considered = []
        available = []
        for entry in self._items:
            contract = entry.contract
            if contract["capability_id"] != wanted:
                continue
            offered = {operation["name"] for operation in contract["operations"]}
            reasons = []
            if not entry.healthy:
                reasons.append("provider_unhealthy")
            if not entry.trusted:
                reasons.append("provider_not_trusted")
            if not _compatible(contract["version"], constraint):
                reasons.append("version_incompatible")
            missing_operations = sorted(operations - offered)
            if missing_operations:
                reasons.append("operations_missing")
            item = {
                "provider_id": contract["provider_id"],
                "version": contract["version"],
                "available": not reasons,
                "reason_codes": reasons,
                "missing_operations": missing_operations,
            }
            considered.append(item)
            if not reasons:
                available.append(contract)

        considered.sort(
            key=lambda provider: (
                _version(provider["version"]),
                provider["provider_id"],
            ),
            reverse=True,
        )
        available.sort(
            key=lambda contract: (
                _version(contract["version"]),
                contract["provider_id"],
            ),
            reverse=True,
        )
        reason_codes = sorted(
            {reason for provider in considered for reason in provider["reason_codes"]}
        )
        if not considered:
            reason_codes = ["provider_not_found"]
        is_available = bool(available)
        return {
            "schema_version": "1.0.0",
            "capability_id": wanted,
            "version_constraint": constraint,
            "required_operations": sorted(operations),
            "available": is_available,
            "selected_provider_id": (
                available[0]["provider_id"] if is_available else None
            ),
            "considered_providers": considered,
            "reason_codes": [] if is_available else reason_codes,
            "summary": (
                "A local provider can supply this capability."
                if is_available
                else "This capability is not currently available."
            ),
            "next_steps": (
                ["Continue to the user review and authorization gates."]
                if is_available
                else self._resolution_next_steps(reason_codes)
            ),
            "brand_allowlist_required": False,
            "custom_hardware_supported": True,
            "can_execute": False,
            "plain_language": True,
        }

    def discover(self) -> Iterable[dict[str, Any]]:
        for entry in sorted(
            self._items,
            key=lambda value: (
                value.contract["capability_id"],
                value.contract["provider_id"],
                _version(value.contract["version"]),
            ),
        ):
            yield deepcopy(entry.contract)

    @staticmethod
    def _resolution_next_steps(reason_codes: list[str]) -> list[str]:
        steps = []
        if "provider_not_found" in reason_codes:
            steps.append("Add or build a local provider that declares this capability.")
        if "provider_unhealthy" in reason_codes:
            steps.append("Check the local provider connection and health.")
        if "provider_not_trusted" in reason_codes:
            steps.append("Review the provider identity and trust evidence.")
        if "version_incompatible" in reason_codes:
            steps.append("Choose a compatible provider or supported version.")
        if "operations_missing" in reason_codes:
            steps.append(
                "Choose or configure a provider that offers the missing operations."
            )
        return steps
