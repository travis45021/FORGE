"""Fail-closed validation for isolated slicer worker manifests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any, ClassVar


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


class SlicerWorkerSupervisor:
    """Convert worker outcomes into deterministic, non-authoritative evidence."""

    OUTCOMES: ClassVar[set[str]] = {
        "completed",
        "crashed",
        "timed_out",
        "cancelled",
    }

    def assess_outcome(
        self,
        manifest: Mapping[str, Any],
        *,
        outcome: str,
        context_id: str,
        current_context_id: str,
        peak_memory_bytes: int,
        disk_written_bytes: int,
        artifact_digest: str | None = None,
    ) -> dict[str, Any]:
        worker = SlicerWorkerBoundary().validate(manifest)
        if outcome not in self.OUTCOMES:
            raise SlicerWorkerError("unknown worker outcome")
        for value, label in (
            (peak_memory_bytes, "peak memory"),
            (disk_written_bytes, "disk written"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise SlicerWorkerError(f"{label} must be a non-negative integer")

        reason = {
            "completed": "worker_completed",
            "crashed": "worker_crashed",
            "timed_out": "worker_timed_out",
            "cancelled": "worker_cancelled",
        }[outcome]
        if context_id != current_context_id:
            reason = "stale_execution_context"
        elif peak_memory_bytes > worker["limits"]["memory_bytes"]:
            reason = "memory_limit_exceeded"
        elif disk_written_bytes > worker["limits"]["disk_bytes"]:
            reason = "disk_limit_exceeded"

        succeeded = reason == "worker_completed"
        if succeeded:
            self._digest(artifact_digest)
        return {
            "schema_version": "1.0.0",
            "worker_id": worker["worker_id"],
            "context": worker["context"],
            "context_id": context_id,
            "status": "succeeded" if succeeded else "failed_closed",
            "reason": reason,
            "artifact_digest": artifact_digest if succeeded else None,
            "artifact_accepted": succeeded,
            "workspace_cleanup_required": True,
            "worker_reuse_allowed": False,
            "retry_requires_fresh_context": not succeeded,
            "can_upload": False,
            "can_start_print": False,
            "can_control_hardware": False,
        }

    @staticmethod
    def _digest(value: Any) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise SlicerWorkerError(
                "completed worker artifact must be lowercase SHA-256"
            )
