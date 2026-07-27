"""FAS-033 manufacturing artifact intake and preflight reference contract."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from .slicing import SlicerContractBoundary, SlicerContractError


class PreflightError(ValueError):
    """Raised when an artifact cannot be safely classified or checked."""


FORMATS = {"step", "stl", "3mf", "gcode", "f3d", "cad"}
SUPPORTED = {"step", "stl", "3mf", "gcode", "cad"}


class ArtifactPreflight:
    """Classify artifacts and produce findings without slicing or printing."""

    def inspect(self, artifact: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(artifact))
        required = {"artifact_id", "filename", "format", "digest", "size_bytes"}
        missing = sorted(required - item.keys())
        if missing:
            raise PreflightError(f"artifact missing: {', '.join(missing)}")
        fmt = str(item["format"]).lower()
        if fmt not in FORMATS:
            raise PreflightError("unsupported artifact format")
        findings: list[str] = []
        if item["size_bytes"] <= 0:
            findings.append("artifact size must be positive")
        if not item["digest"].startswith("sha256:"):
            findings.append("artifact digest must be sha256")
        if fmt == "f3d":
            findings.append("F3D architecture is deferred; use STEP or 3MF")
        if fmt == "gcode":
            findings.append(
                "G-code is inspectable input and is not trusted toolpath authority"
            )
        if fmt not in SUPPORTED:
            findings.append("format requires deferred integration")
        return {
            "artifact_id": item["artifact_id"],
            "format": fmt,
            "status": "needs_review" if findings else "accepted_for_validation",
            "findings": findings,
            "source_digest": item["digest"],
            "slicing_authorized": False,
            "print_authorized": False,
        }

    def validate(
        self, artifact: Mapping[str, Any], *, checks: Mapping[str, bool]
    ) -> dict[str, Any]:
        result = self.inspect(artifact)
        failed = sorted(name for name, passed in checks.items() if passed is not True)
        result["validation_checks"] = dict(checks)
        result["validation_status"] = (
            "passed"
            if not failed and result["status"] == "accepted_for_validation"
            else "failed"
        )
        if failed:
            result["findings"].extend(f"validation failed: {name}" for name in failed)
        result["requires_user_review"] = True
        return result

    def inspect_slicer_output(
        self,
        output_path: str | Path,
        result: Mapping[str, Any],
        *,
        expected_request_id: str,
        expected_context: str,
    ) -> dict[str, Any]:
        """Bind output bytes to one validated slicer-result contract."""
        path = Path(output_path)
        if not path.is_file() or path.is_symlink():
            raise PreflightError("slicer output must be a regular file")
        if path.stat().st_size <= 0:
            raise PreflightError("slicer output must not be empty")
        try:
            slicer_result = SlicerContractBoundary().result(result)
        except SlicerContractError as exc:
            raise PreflightError(str(exc)) from exc
        if slicer_result["status"] != "succeeded":
            raise PreflightError("only successful slicer output can pass preflight")
        if slicer_result["request_id"] != expected_request_id:
            raise PreflightError("slicer output belongs to a different request")
        if slicer_result["context"] != expected_context:
            raise PreflightError("slicer output belongs to a stale or wrong context")

        measured_digest = sha256(path.read_bytes()).hexdigest()
        if slicer_result.get("artifact_digest") != measured_digest:
            raise PreflightError("slicer output bytes do not match the recorded digest")
        return {
            "schema_version": "1.0.0",
            "request_id": expected_request_id,
            "context": expected_context,
            "artifact_digest": measured_digest,
            "size_bytes": path.stat().st_size,
            "engine": deepcopy(slicer_result["engine"]),
            "warnings": deepcopy(slicer_result["warnings"]),
            "status": "passed",
            "result_contract_validated": True,
            "output_digest_verified": True,
            "requires_twin_comparison": True,
            "can_authorize_production": False,
            "can_upload": False,
            "can_start_print": False,
        }

    def inspect_worker_pair_outputs(
        self,
        pair_outcome: Mapping[str, Any],
        *,
        production_path: str | Path,
        production_result: Mapping[str, Any],
        twin_path: str | Path,
        twin_result: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Preflight both outputs only when their coordinated pair succeeded."""
        pair = deepcopy(dict(pair_outcome))
        if (
            pair.get("status") != "ready_for_preflight"
            or pair.get("artifacts_eligible_for_preflight") is not True
            or pair.get("can_compare") is not True
            or pair.get("can_upload") is not False
            or pair.get("can_start_print") is not False
            or pair.get("can_control_hardware") is not False
        ):
            raise PreflightError("worker pair is not eligible for preflight")

        evidence: dict[str, dict[str, Any]] = {}
        for context, path, result in (
            ("production", production_path, production_result),
            ("twin", twin_path, twin_result),
        ):
            outcome = pair.get(context)
            if (
                not isinstance(outcome, Mapping)
                or outcome.get("status") != "succeeded"
                or not outcome.get("request_id")
            ):
                raise PreflightError(f"{context} worker outcome is not trusted")
            checked = self.inspect_slicer_output(
                path,
                result,
                expected_request_id=str(outcome["request_id"]),
                expected_context=context,
            )
            if checked["artifact_digest"] != outcome.get("artifact_digest"):
                raise PreflightError(
                    f"{context} output does not match the successful worker outcome"
                )
            self._same_engine(checked["engine"], pair.get("engine"), context)
            evidence[context] = checked

        return {
            "schema_version": "1.0.0",
            "status": "ready_for_comparison",
            "engine": deepcopy(pair["engine"]),
            "input_digest": pair.get("input_digest"),
            "profile_digest": pair.get("profile_digest"),
            "production": evidence["production"],
            "twin": evidence["twin"],
            "pair_outcome_validated": True,
            "both_output_digests_verified": True,
            "can_upload": False,
            "can_start_print": False,
            "can_authorize_production": False,
        }

    @staticmethod
    def _same_engine(result_engine: Any, pair_engine: Any, context: str) -> None:
        if not isinstance(result_engine, Mapping) or not isinstance(
            pair_engine, Mapping
        ):
            raise PreflightError(f"{context} engine provenance is invalid")
        fields = ("name", "version", "source_digest")
        if any(result_engine.get(field) != pair_engine.get(field) for field in fields):
            raise PreflightError(
                f"{context} output came from a different reviewed engine"
            )
