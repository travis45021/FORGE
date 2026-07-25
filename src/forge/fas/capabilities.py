"""Deterministic FAS-003 capability registry."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping


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
        if not names or any(not name for name in names) or len(names) != len(set(names)):
            raise CapabilityError("operations must have unique names")
        key = (item["capability_id"], item["version"], item["provider_id"])
        if any(
            (entry.contract["capability_id"], entry.contract["version"], entry.contract["provider_id"]) == key
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
            key=lambda entry: (_version(entry.contract["version"]), entry.contract["provider_id"]),
            reverse=True,
        )
        return deepcopy(candidates[0].contract)

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
