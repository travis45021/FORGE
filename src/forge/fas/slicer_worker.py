"""Fail-closed validation for isolated slicer worker manifests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any


class SlicerWorkerError(ValueError):
    """Raised when a slicer worker manifest violates isolation rules."""


REQUIRED_FORBIDDEN = {
    "printer_control",
    "printer_discovery",
    "cloud_access",
    "telemetry",
    "self_update",
}


class SlicerWorkerBoundary:
    """Validate worker isolation without launching an engine process."""

    def validate(self, value: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(value))
        required = {
            "worker_id",
            "context",
            "workspace",
            "limits",
            "forbidden_capabilities",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise SlicerWorkerError(f"worker manifest missing: {', '.join(missing)}")
        if not item["worker_id"] or item["context"] not in {"production", "twin"}:
            raise SlicerWorkerError("worker identity or context is invalid")

        workspace = item["workspace"]
        if not isinstance(workspace, Mapping):
            raise SlicerWorkerError("worker workspace must be an object")
        paths = []
        for key in ("input", "output", "logs"):
            raw = workspace.get(key)
            if not isinstance(raw, str) or not raw:
                raise SlicerWorkerError(f"workspace {key} path is required")
            paths.append(Path(raw))
        if len({path.resolve() for path in paths}) != 3:
            raise SlicerWorkerError("worker input, output, and logs must be separate")

        limits = item["limits"]
        if not isinstance(limits, Mapping):
            raise SlicerWorkerError("worker limits must be an object")
        for key in ("timeout_seconds", "memory_bytes", "disk_bytes"):
            limit = limits.get(key)
            if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
                raise SlicerWorkerError(f"worker {key} must be a positive integer")

        forbidden = item["forbidden_capabilities"]
        if (
            not isinstance(forbidden, Sequence)
            or isinstance(forbidden, (str, bytes))
            or not REQUIRED_FORBIDDEN.issubset(forbidden)
        ):
            raise SlicerWorkerError("worker forbidden capabilities are incomplete")
        item["can_control_hardware"] = False
        return item

    def validate_pair(
        self, production: Mapping[str, Any], twin: Mapping[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        production_item = self.validate(production)
        twin_item = self.validate(twin)
        if production_item["context"] != "production" or twin_item["context"] != "twin":
            raise SlicerWorkerError("worker pair contexts are invalid")
        production_paths = set(production_item["workspace"].values())
        twin_paths = set(twin_item["workspace"].values())
        if production_paths & twin_paths:
            raise SlicerWorkerError("production and twin workspaces must not overlap")
        return production_item, twin_item
