"""FAS-033 manufacturing artifact intake and preflight reference contract."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


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
