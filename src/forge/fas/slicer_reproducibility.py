"""Deterministic comparison of repeated slicer results."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from hashlib import sha256
from typing import Any

from .slicing import SlicerContractBoundary, SlicerContractError


class SlicerReproducibilityError(ValueError):
    """Raised when repeated-run evidence is incomplete or incomparable."""


def reproducibility_evidence_digest(value: Mapping[str, Any]) -> str:
    """Hash reproducibility evidence without including its own digest."""
    item = deepcopy(dict(value))
    item.pop("evidence_digest", None)
    canonical = json.dumps(
        item,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


class SlicerReproducibilityService:
    """Compare repeated outcomes without granting production authority."""

    def evaluate(
        self,
        *,
        run_group_id: str,
        input_digest: str,
        profile_digest: str,
        results: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        if not run_group_id.strip():
            raise SlicerReproducibilityError("run group identity is required")
        self._digest(input_digest, "input digest")
        self._digest(profile_digest, "profile digest")
        if isinstance(results, (str, bytes)) or len(results) < 2:
            raise SlicerReproducibilityError(
                "at least two repeated slicer results are required"
            )

        validated = []
        for value in results:
            try:
                item = SlicerContractBoundary().result(value)
            except (SlicerContractError, TypeError) as exc:
                raise SlicerReproducibilityError(str(exc)) from exc
            if item["status"] != "succeeded":
                raise SlicerReproducibilityError(
                    "reproducibility requires successful repeated runs"
                )
            self._digest(item.get("artifact_digest"), "artifact digest")
            validated.append(item)

        contexts = {item["context"] for item in validated}
        engines = {
            (
                item["engine"]["name"],
                item["engine"]["version"],
                item["engine"]["source_digest"],
                item["engine"]["build_digest"],
            )
            for item in validated
        }
        if len(contexts) != 1:
            raise SlicerReproducibilityError(
                "repeated runs must use the same execution context"
            )
        if len(engines) != 1:
            raise SlicerReproducibilityError(
                "repeated runs must use the same engine source and build"
            )
        request_ids = [item["request_id"] for item in validated]
        if len(set(request_ids)) != len(request_ids):
            raise SlicerReproducibilityError(
                "repeated runs must have distinct request identities"
            )

        artifact_digests = [item["artifact_digest"] for item in validated]
        warning_sets = [item["warnings"] for item in validated]
        artifacts_match = len(set(artifact_digests)) == 1
        warnings_match = all(warnings == warning_sets[0] for warnings in warning_sets)
        reproducible = artifacts_match and warnings_match
        engine = validated[0]["engine"]
        result = {
            "schema_version": "1.0.0",
            "run_group_id": run_group_id,
            "context": validated[0]["context"],
            "input_digest": input_digest,
            "profile_digest": profile_digest,
            "engine": deepcopy(engine),
            "run_count": len(validated),
            "request_ids": request_ids,
            "artifact_digests": artifact_digests,
            "warning_sets": deepcopy(warning_sets),
            "artifacts_match": artifacts_match,
            "warnings_match": warnings_match,
            "reproducible": reproducible,
            "reason": (
                "repeated_results_match"
                if reproducible
                else (
                    "artifact_digest_mismatch"
                    if not artifacts_match
                    else "warning_mismatch"
                )
            ),
            "real_engine_runs_required": True,
            "can_authorize_production": False,
            "can_upload": False,
            "can_start_print": False,
        }
        result["evidence_digest"] = reproducibility_evidence_digest(result)
        return result

    @staticmethod
    def _digest(value: Any, label: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise SlicerReproducibilityError(f"{label} must be lowercase SHA-256")
