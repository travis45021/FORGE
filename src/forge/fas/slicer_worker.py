"""Fail-closed validation for isolated slicer worker manifests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import PurePosixPath
from typing import Any, ClassVar

from .slicing import SlicerContractBoundary, SlicerContractError


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
        if set(workspace) != {"input", "output", "logs"}:
            raise SlicerWorkerError("worker workspace fields are invalid")
        paths: dict[str, PurePosixPath] = {}
        for key in ("input", "output", "logs"):
            raw = workspace.get(key)
            if not isinstance(raw, str) or not raw:
                raise SlicerWorkerError(f"workspace {key} path is required")
            path = self._workspace_path(raw)
            if path.name != key:
                raise SlicerWorkerError(f"workspace {key} path must end in /{key}")
            paths[key] = path
        if len(set(paths.values())) != 3:
            raise SlicerWorkerError("worker input, output, and logs must be separate")
        roots = {path.parent for path in paths.values()}
        if len(roots) != 1 or len(next(iter(roots)).parts) < 2:
            raise SlicerWorkerError(
                "worker paths must share one dedicated relative workspace root"
            )
        item["workspace"] = {key: path.as_posix() for key, path in paths.items()}

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
        production_root = PurePosixPath(production_item["workspace"]["input"]).parent
        twin_root = PurePosixPath(twin_item["workspace"]["input"]).parent
        if self._contains(production_root, twin_root) or self._contains(
            twin_root, production_root
        ):
            raise SlicerWorkerError("production and twin workspaces must not overlap")
        return production_item, twin_item

    def assign(
        self,
        manifest: Mapping[str, Any],
        request: Mapping[str, Any],
        profile: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Bind an isolated worker to one request and one ephemeral profile."""
        worker = self.validate(manifest)
        try:
            slicer_request = SlicerContractBoundary().request(request)
        except SlicerContractError as exc:
            raise SlicerWorkerError(str(exc)) from exc
        if slicer_request["context"] != worker["context"]:
            raise SlicerWorkerError("worker and request contexts do not match")
        input_value = slicer_request.get("input")
        input_path_value = (
            input_value.get("path") if isinstance(input_value, Mapping) else None
        )
        if not isinstance(input_path_value, str):
            raise SlicerWorkerError("slicer request input path is required")
        input_path = self._workspace_path(input_path_value)
        input_root = PurePosixPath(worker["workspace"]["input"])
        if not self._contains(input_root, input_path) or input_path == input_root:
            raise SlicerWorkerError(
                "slicer request input must stay inside its assigned workspace"
            )
        profile_item = dict(profile)
        if slicer_request.get("profile_ephemeral") is not True:
            raise SlicerWorkerError("slicer request must declare an ephemeral profile")
        if slicer_request["profile_digest"] != profile_item.get("profile_digest"):
            raise SlicerWorkerError("worker profile digest does not match request")
        if (
            profile_item.get("lifecycle") != "ephemeral"
            or profile_item.get("persist_after_worker") is not False
            or profile_item.get("delete_after_result") is not True
            or profile_item.get("contains_transport_endpoint") is not False
            or profile_item.get("contains_credentials") is not False
            or profile_item.get("cloud_access") is not False
            or profile_item.get("can_control_printer") is not False
            or profile_item.get("can_upload") is not False
            or profile_item.get("can_start_print") is not False
        ):
            raise SlicerWorkerError("worker profile violates isolation or authority")
        return {
            "schema_version": "1.0.0",
            "worker_id": worker["worker_id"],
            "request_id": slicer_request["request_id"],
            "context": worker["context"],
            "profile_digest": slicer_request["profile_digest"],
            "workspace": deepcopy(worker["workspace"]),
            "limits": deepcopy(worker["limits"]),
            "single_use": True,
            "profile_delete_after_result": True,
            "can_control_hardware": False,
            "can_upload": False,
            "can_start_print": False,
        }

    def assign_pair(
        self,
        *,
        production_manifest: Mapping[str, Any],
        twin_manifest: Mapping[str, Any],
        production_request: Mapping[str, Any],
        twin_request: Mapping[str, Any],
        profile: Mapping[str, Any],
        engine: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Bind isolated contexts to one engine, input, and derived profile."""
        production_worker, twin_worker = self.validate_pair(
            production_manifest, twin_manifest
        )
        production = self.assign(production_worker, production_request, profile)
        twin = self.assign(twin_worker, twin_request, profile)
        production_input = production_request.get("input")
        twin_input = twin_request.get("input")
        if not isinstance(production_input, Mapping) or not isinstance(
            twin_input, Mapping
        ):
            raise SlicerWorkerError("worker pair inputs are required")
        if production_input.get("digest") != twin_input.get("digest"):
            raise SlicerWorkerError("production and twin input digests must match")
        if production["profile_digest"] != twin["profile_digest"]:
            raise SlicerWorkerError("production and twin profile digests must match")

        engine_item = deepcopy(dict(engine))
        required_engine = {"name", "version", "source_digest", "build_digest"}
        missing = sorted(required_engine - engine_item.keys())
        if missing:
            raise SlicerWorkerError(f"reviewed engine missing: {', '.join(missing)}")
        for field in ("source_digest", "build_digest"):
            self._digest(engine_item[field], f"engine {field}")
        return {
            "schema_version": "1.0.0",
            "engine": engine_item,
            "input_digest": production_input["digest"],
            "profile_digest": production["profile_digest"],
            "production": production,
            "twin": twin,
            "workspaces_isolated": True,
            "same_engine_build": True,
            "same_input": True,
            "same_profile": True,
            "can_control_hardware": False,
            "can_upload": False,
            "can_start_print": False,
        }

    @staticmethod
    def _digest(value: Any, label: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise SlicerWorkerError(f"{label} must be lowercase SHA-256")

    @staticmethod
    def _workspace_path(value: str) -> PurePosixPath:
        components = value.split("/")
        if (
            value.startswith("/")
            or "\\" in value
            or ":" in value
            or any(component in {"", ".", ".."} for component in components)
        ):
            raise SlicerWorkerError(
                "worker paths must be canonical relative POSIX paths"
            )
        return PurePosixPath(value)

    @staticmethod
    def _contains(parent: PurePosixPath, child: PurePosixPath) -> bool:
        parent_parts = parent.parts
        return child.parts[: len(parent_parts)] == parent_parts


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

    def assess_pair(
        self,
        assignment: Mapping[str, Any],
        *,
        production: Mapping[str, Any],
        twin: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Fail the whole pair when either isolated worker is not successful."""
        pair = dict(assignment)
        if (
            pair.get("workspaces_isolated") is not True
            or pair.get("same_engine_build") is not True
            or pair.get("same_input") is not True
            or pair.get("same_profile") is not True
            or pair.get("can_control_hardware") is not False
            or pair.get("can_upload") is not False
            or pair.get("can_start_print") is not False
        ):
            raise SlicerWorkerError("worker pair assignment is not trusted")
        production_item = self._pair_outcome(
            production, pair.get("production"), "production"
        )
        twin_item = self._pair_outcome(twin, pair.get("twin"), "twin")
        succeeded = (
            production_item["status"] == "succeeded"
            and twin_item["status"] == "succeeded"
        )
        return {
            "schema_version": "1.0.0",
            "engine": deepcopy(pair.get("engine")),
            "input_digest": pair.get("input_digest"),
            "profile_digest": pair.get("profile_digest"),
            "status": "ready_for_preflight" if succeeded else "failed_closed",
            "production": deepcopy(production_item),
            "twin": deepcopy(twin_item),
            "cancel_remaining_worker": not succeeded,
            "artifacts_eligible_for_preflight": succeeded,
            "retry_requires_fresh_pair": not succeeded,
            "can_compare": succeeded,
            "can_upload": False,
            "can_start_print": False,
            "can_control_hardware": False,
        }

    @staticmethod
    def _pair_outcome(
        outcome: Mapping[str, Any],
        assigned: Any,
        context: str,
    ) -> dict[str, Any]:
        if not isinstance(assigned, Mapping):
            raise SlicerWorkerError(f"{context} worker assignment is missing")
        item = dict(outcome)
        if (
            item.get("worker_id") != assigned.get("worker_id")
            or item.get("context") != context
            or item.get("can_upload") is not False
            or item.get("can_start_print") is not False
            or item.get("can_control_hardware") is not False
            or item.get("status") not in {"succeeded", "failed_closed"}
        ):
            raise SlicerWorkerError(f"{context} worker outcome is invalid")
        item["request_id"] = assigned.get("request_id")
        item["profile_digest"] = assigned.get("profile_digest")
        item["workspace"] = deepcopy(assigned.get("workspace"))
        item["limits"] = deepcopy(assigned.get("limits"))
        return item

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
