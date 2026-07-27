"""Accept slicer evidence for review without authorizing physical work."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class SlicerAcceptanceError(ValueError):
    """Raised when slicer evidence is not ready for the final user gate."""


class SlicerArtifactAcceptance:
    """Turn reviewed comparison evidence into non-authoritative readiness."""

    def accept(self, comparison: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(comparison))
        if item.get("can_authorize_production") is not False:
            raise SlicerAcceptanceError("comparison evidence must be non-authoritative")
        production = item.get("production")
        twin = item.get("twin")
        acceptance = item.get("acceptance")
        if not all(
            isinstance(value, Mapping) for value in (production, twin, acceptance)
        ):
            raise SlicerAcceptanceError("comparison evidence is incomplete")
        if production.get("context") != "production" or twin.get("context") != "twin":
            raise SlicerAcceptanceError("comparison contexts are invalid")
        if production.get("status") != "succeeded" or twin.get("status") != "succeeded":
            raise SlicerAcceptanceError("both slicer contexts must succeed")
        artifact_digest = production.get("artifact_digest")
        if not self._digest(artifact_digest):
            raise SlicerAcceptanceError("production artifact digest is required")
        input_digest = item.get("input_digest")
        profile_digest = item.get("profile_digest")
        if not self._digest(input_digest) or not self._digest(profile_digest):
            raise SlicerAcceptanceError(
                "accepted artifact requires input and profile lineage"
            )
        engine = production.get("engine")
        if not isinstance(engine, Mapping):
            raise SlicerAcceptanceError("accepted artifact requires engine provenance")
        engine_source_digest = engine.get("source_digest")
        engine_build_digest = engine.get("build_digest")
        if not self._digest(engine_source_digest) or not self._digest(
            engine_build_digest
        ):
            raise SlicerAcceptanceError(
                "accepted artifact requires exact engine source and build provenance"
            )
        if acceptance.get("status") != "matching":
            raise SlicerAcceptanceError("production and twin artifacts must match")
        if acceptance.get("preflight_evidence_required") is not True:
            raise SlicerAcceptanceError(
                "acceptance requires deterministic preflight evidence"
            )
        if (
            item.get("pair_preflight_verified") is not True
            or acceptance.get("pair_preflight_required") is not True
        ):
            raise SlicerAcceptanceError(
                "acceptance requires coordinated production and twin preflight"
            )
        if (
            production.get("preflight_verified") is not True
            or twin.get("preflight_verified") is not True
        ):
            raise SlicerAcceptanceError(
                "both production and twin artifacts require verified preflight"
            )
        if acceptance.get("reviewed_by_user") is not True:
            raise SlicerAcceptanceError("user review is required")
        return {
            "comparison_id": item.get("comparison_id"),
            "artifact_digest": artifact_digest,
            "input_digest": input_digest,
            "profile_digest": profile_digest,
            "engine_source_digest": engine_source_digest,
            "engine_build_digest": engine_build_digest,
            "preflight_verified": True,
            "pair_preflight_verified": True,
            "ready_for_live_checks": True,
            "final_confirmation_required": True,
            "can_upload": False,
            "can_start_print": False,
        }

    @staticmethod
    def _digest(value: Any) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )
