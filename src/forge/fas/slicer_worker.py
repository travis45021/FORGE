"""Fail-closed validation for isolated slicer worker manifests."""

from __future__ import annotations

from collections.abc import Mapping
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
        allowed = required | {"can_control_hardware"}
        unexpected = sorted(item.keys() - allowed)
        if unexpected:
            raise SlicerWorkerError(
                f"worker manifest has unknown fields: {', '.join(unexpected)}"
            )
        if "can_control_hardware" in item and item["can_control_hardware"] is not False:
            raise SlicerWorkerError("worker cannot claim hardware control")
        if (
            not isinstance(item["worker_id"], str)
            or not item["worker_id"].strip()
            or item["context"] not in {"production", "twin"}
        ):
            raise SlicerWorkerError("worker identity or context is invalid")
        item["worker_id"] = item["worker_id"].strip()

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
        if set(limits) != {"timeout_seconds", "memory_bytes", "disk_bytes"}:
            raise SlicerWorkerError("worker limit fields are invalid")
        for key in ("timeout_seconds", "memory_bytes", "disk_bytes"):
            limit = limits.get(key)
            if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
                raise SlicerWorkerError(f"worker {key} must be a positive integer")

        forbidden = item["forbidden_capabilities"]
        if (
            not isinstance(forbidden, list)
            or any(not isinstance(value, str) or not value for value in forbidden)
            or len(forbidden) != len(set(forbidden))
            or not REQUIRED_FORBIDDEN.issubset(forbidden)
        ):
            raise SlicerWorkerError("worker forbidden capabilities are incomplete")
        item["forbidden_capabilities"] = sorted(forbidden)
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

    def validate_pair_assignment(self, assignment: Mapping[str, Any]) -> dict[str, Any]:
        """Revalidate a sanitized pair before supervisor composition."""
        pair = deepcopy(dict(assignment))
        required = {
            "schema_version",
            "engine",
            "input_digest",
            "profile_digest",
            "production",
            "twin",
            "workspaces_isolated",
            "same_engine_build",
            "same_input",
            "same_profile",
            "can_control_hardware",
            "can_upload",
            "can_start_print",
        }
        if set(pair) != required or pair.get("schema_version") != "1.0.0":
            raise SlicerWorkerError("worker pair assignment fields are invalid")
        for field in (
            "workspaces_isolated",
            "same_engine_build",
            "same_input",
            "same_profile",
        ):
            if pair[field] is not True:
                raise SlicerWorkerError("worker pair assignment is not trusted")
        for field in ("can_control_hardware", "can_upload", "can_start_print"):
            if pair[field] is not False:
                raise SlicerWorkerError("worker pair assignment is not trusted")
        self._digest(pair["input_digest"], "pair input digest")
        self._digest(pair["profile_digest"], "pair profile digest")

        engine = pair["engine"]
        engine_fields = {"name", "version", "source_digest", "build_digest"}
        if (
            not isinstance(engine, Mapping)
            or set(engine) != engine_fields
            or any(
                not isinstance(engine[field], str) or not engine[field]
                for field in ("name", "version")
            )
        ):
            raise SlicerWorkerError("worker pair engine is invalid")
        self._digest(engine["source_digest"], "engine source digest")
        self._digest(engine["build_digest"], "engine build digest")

        roots = []
        for context in ("production", "twin"):
            worker = pair[context]
            worker_fields = {
                "schema_version",
                "worker_id",
                "request_id",
                "context",
                "profile_digest",
                "workspace",
                "limits",
                "single_use",
                "profile_delete_after_result",
                "can_control_hardware",
                "can_upload",
                "can_start_print",
            }
            if (
                not isinstance(worker, Mapping)
                or set(worker) != worker_fields
                or worker.get("schema_version") != "1.0.0"
                or worker.get("context") != context
                or not isinstance(worker.get("worker_id"), str)
                or not worker["worker_id"]
                or not isinstance(worker.get("request_id"), str)
                or not worker["request_id"]
                or worker.get("profile_digest") != pair["profile_digest"]
                or worker.get("single_use") is not True
                or worker.get("profile_delete_after_result") is not True
                or worker.get("can_control_hardware") is not False
                or worker.get("can_upload") is not False
                or worker.get("can_start_print") is not False
            ):
                raise SlicerWorkerError(f"{context} worker assignment is invalid")
            workspace = worker["workspace"]
            if not isinstance(workspace, Mapping) or set(workspace) != {
                "input",
                "output",
                "logs",
            }:
                raise SlicerWorkerError(f"{context} worker workspace is invalid")
            paths = {
                name: self._workspace_path(value)
                for name, value in workspace.items()
                if isinstance(value, str)
            }
            if (
                set(paths) != {"input", "output", "logs"}
                or any(paths[name].name != name for name in paths)
                or len({path.parent for path in paths.values()}) != 1
            ):
                raise SlicerWorkerError(f"{context} worker workspace is invalid")
            roots.append(paths["input"].parent)
            limits = worker["limits"]
            if (
                not isinstance(limits, Mapping)
                or set(limits)
                != {
                    "timeout_seconds",
                    "memory_bytes",
                    "disk_bytes",
                }
                or any(
                    not isinstance(value, int) or isinstance(value, bool) or value <= 0
                    for value in limits.values()
                )
            ):
                raise SlicerWorkerError(f"{context} worker limits are invalid")
        if self._contains(roots[0], roots[1]) or self._contains(roots[1], roots[0]):
            raise SlicerWorkerError("production and twin workspaces must not overlap")
        return pair

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

    def assess_process_evidence(
        self,
        manifest: Mapping[str, Any],
        evidence: Mapping[str, Any],
        *,
        context_id: str,
        current_context_id: str,
        peak_memory_bytes: int,
        disk_written_bytes: int,
        artifact_digest: str | None = None,
    ) -> dict[str, Any]:
        """Convert local supervisor evidence into a worker outcome.

        This adapter validates the contract-only process evidence before it
        reaches the worker fault policy. It does not claim that OS resource
        limits were enforced or that a process produced a trusted artifact.
        """
        item = dict(evidence)
        required = {
            "schema_version",
            "outcome",
            "returncode",
            "stdout_bytes",
            "stderr_bytes",
            "stdout_digest",
            "stderr_digest",
            "shell_used",
            "physical_commands_allowed",
            "release_authority_granted",
            "worker_reuse_allowed",
            "resource_limits_enforced",
            "requires_reviewed_resource_supervisor",
        }
        if set(item) != required or item.get("schema_version") != "1.0.0":
            raise SlicerWorkerError("process evidence fields are invalid")
        outcome = item.get("outcome")
        if outcome not in self.OUTCOMES:
            raise SlicerWorkerError("process evidence outcome is invalid")
        if (
            not isinstance(item.get("returncode"), int)
            or isinstance(item.get("returncode"), bool)
            or not isinstance(item.get("stdout_bytes"), int)
            or isinstance(item.get("stdout_bytes"), bool)
            or item["stdout_bytes"] < 0
            or not isinstance(item.get("stderr_bytes"), int)
            or isinstance(item.get("stderr_bytes"), bool)
            or item["stderr_bytes"] < 0
            or not self._is_digest(item.get("stdout_digest"))
            or not self._is_digest(item.get("stderr_digest"))
        ):
            raise SlicerWorkerError("process evidence values are invalid")
        for field in (
            "shell_used",
            "physical_commands_allowed",
            "release_authority_granted",
            "worker_reuse_allowed",
            "resource_limits_enforced",
        ):
            if item.get(field) is not False:
                raise SlicerWorkerError("process evidence grants unsafe authority")
        if item.get("requires_reviewed_resource_supervisor") is not True:
            raise SlicerWorkerError("process evidence must require resource review")
        if outcome == "completed" and item["returncode"] != 0:
            raise SlicerWorkerError("completed process evidence has nonzero returncode")
        if outcome != "completed" and item["returncode"] == 0:
            raise SlicerWorkerError("failed process evidence has zero returncode")
        return self.assess_outcome(
            manifest,
            outcome=outcome,
            context_id=context_id,
            current_context_id=current_context_id,
            peak_memory_bytes=peak_memory_bytes,
            disk_written_bytes=disk_written_bytes,
            artifact_digest=artifact_digest,
        )

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
        pair = SlicerWorkerBoundary().validate_pair_assignment(assignment)
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
        required = {
            "schema_version",
            "worker_id",
            "context",
            "context_id",
            "status",
            "reason",
            "artifact_digest",
            "artifact_accepted",
            "workspace_cleanup_required",
            "worker_reuse_allowed",
            "retry_requires_fresh_context",
            "can_upload",
            "can_start_print",
            "can_control_hardware",
        }
        if set(item) != required:
            raise SlicerWorkerError(f"{context} worker outcome fields are invalid")
        if (
            item.get("schema_version") != "1.0.0"
            or item.get("worker_id") != assigned.get("worker_id")
            or item.get("context") != context
            or not isinstance(item.get("context_id"), str)
            or not item["context_id"]
            or item.get("can_upload") is not False
            or item.get("can_start_print") is not False
            or item.get("can_control_hardware") is not False
            or item.get("status") not in {"succeeded", "failed_closed"}
            or item.get("workspace_cleanup_required") is not True
            or item.get("worker_reuse_allowed") is not False
        ):
            raise SlicerWorkerError(f"{context} worker outcome is invalid")
        if item["status"] == "succeeded":
            if (
                item.get("reason") != "worker_completed"
                or item.get("artifact_accepted") is not True
                or item.get("retry_requires_fresh_context") is not False
            ):
                raise SlicerWorkerError(
                    f"{context} successful worker outcome is inconsistent"
                )
            SlicerWorkerSupervisor._digest(item.get("artifact_digest"))
        elif (
            item.get("reason")
            not in {
                "worker_crashed",
                "worker_timed_out",
                "worker_cancelled",
                "stale_execution_context",
                "memory_limit_exceeded",
                "disk_limit_exceeded",
            }
            or item.get("artifact_digest") is not None
            or item.get("artifact_accepted") is not False
            or item.get("retry_requires_fresh_context") is not True
        ):
            raise SlicerWorkerError(f"{context} failed worker outcome is inconsistent")
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

    @staticmethod
    def _is_digest(value: Any) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 71
            and value.startswith("sha256:")
            and all(character in "0123456789abcdef" for character in value[7:])
        )
