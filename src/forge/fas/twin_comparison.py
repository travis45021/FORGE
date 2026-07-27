"""Production/twin comparison evidence without authorization power."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from typing import Any

from .slicing import SlicerContractBoundary, SlicerContractError


class TwinComparisonError(ValueError):
    """Raised when production and twin evidence cannot be safely compared."""


def comparison_evidence_digest(value: Mapping[str, Any]) -> str:
    """Hash the complete comparison so later review cannot change silently."""
    item = deepcopy(dict(value))
    item.pop("evidence_digest", None)
    canonical = json.dumps(
        item,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


class TwinComparisonService:
    """Compare isolated results and report differences as evidence only."""

    def __init__(self) -> None:
        self._boundary = SlicerContractBoundary()

    def compare(
        self,
        *,
        comparison_id: str,
        input_digest: str,
        production: Mapping[str, Any],
        twin: Mapping[str, Any],
        reviewed_by_user: bool = False,
    ) -> dict[str, Any]:
        if not comparison_id:
            raise TwinComparisonError("comparison identity is required")
        self._digest(input_digest)
        try:
            production_result = self._boundary.result(production)
            twin_result = self._boundary.result(twin)
        except SlicerContractError as exc:
            raise TwinComparisonError(str(exc)) from exc
        if production_result["context"] != "production":
            raise TwinComparisonError("production result has the wrong context")
        if twin_result["context"] != "twin":
            raise TwinComparisonError("twin result has the wrong context")

        differences: list[str] = []
        for field in ("status", "artifact_digest", "warnings"):
            if production_result.get(field) != twin_result.get(field):
                differences.append(field)
        if production_result["engine"] != twin_result["engine"]:
            differences.append("engine")

        status = "matching" if not differences else "different"
        if (
            production_result["status"] != "succeeded"
            or twin_result["status"] != "succeeded"
        ):
            status = "inconclusive"
        return {
            "comparison_id": comparison_id,
            "input_digest": input_digest,
            "production": production_result,
            "twin": twin_result,
            "differences": differences,
            "acceptance": {
                "status": status,
                "reviewed_by_user": reviewed_by_user,
            },
            "can_authorize_production": False,
        }

    def compare_preflighted(
        self,
        *,
        comparison_id: str,
        input_digest: str,
        production: Mapping[str, Any],
        twin: Mapping[str, Any],
        reviewed_by_user: bool = False,
    ) -> dict[str, Any]:
        """Compare measured, preflighted artifacts instead of raw claims."""
        production_evidence = self._preflight(production, "production")
        twin_evidence = self._preflight(twin, "twin")
        differences = []
        for field in ("artifact_digest", "engine", "warnings"):
            if production_evidence[field] != twin_evidence[field]:
                differences.append(field)
        return {
            "comparison_id": comparison_id,
            "input_digest": input_digest,
            "production": {
                **production_evidence,
                "status": "succeeded",
                "authority": {"can_upload": False, "can_start_print": False},
            },
            "twin": {
                **twin_evidence,
                "status": "succeeded",
                "authority": {"can_upload": False, "can_start_print": False},
            },
            "differences": differences,
            "acceptance": {
                "status": "matching" if not differences else "different",
                "reviewed_by_user": reviewed_by_user,
                "preflight_evidence_required": True,
            },
            "can_authorize_production": False,
        }

    def compare_paired_preflight(
        self,
        *,
        comparison_id: str,
        paired_preflight: Mapping[str, Any],
        reviewed_by_user: bool = False,
    ) -> dict[str, Any]:
        """Compare only evidence emitted by coordinated paired preflight."""
        if reviewed_by_user is True:
            raise TwinComparisonError(
                "user review must be recorded by the click-three presentation"
            )
        pair = dict(paired_preflight)
        if (
            pair.get("status") != "ready_for_comparison"
            or pair.get("pair_outcome_validated") is not True
            or pair.get("both_output_digests_verified") is not True
            or pair.get("can_authorize_production") is not False
            or pair.get("can_upload") is not False
            or pair.get("can_start_print") is not False
        ):
            raise TwinComparisonError(
                "comparison requires coordinated paired preflight"
            )
        production = pair.get("production")
        twin = pair.get("twin")
        if not isinstance(production, Mapping) or not isinstance(twin, Mapping):
            raise TwinComparisonError("paired preflight evidence is incomplete")
        result = self.compare_preflighted(
            comparison_id=comparison_id,
            input_digest=pair.get("input_digest"),
            production=production,
            twin=twin,
            reviewed_by_user=reviewed_by_user,
        )
        result["profile_digest"] = pair.get("profile_digest")
        result["pair_preflight_verified"] = True
        result["acceptance"]["pair_preflight_required"] = True
        result["evidence_digest"] = comparison_evidence_digest(result)
        return result

    @staticmethod
    def _preflight(value: Mapping[str, Any], context: str) -> dict[str, Any]:
        item = dict(value)
        if (
            item.get("status") != "passed"
            or item.get("result_contract_validated") is not True
            or item.get("output_digest_verified") is not True
            or item.get("can_authorize_production") is not False
            or item.get("can_upload") is not False
            or item.get("can_start_print") is not False
        ):
            raise TwinComparisonError(
                f"{context} artifact has not passed deterministic preflight"
            )
        if item.get("context") != context:
            raise TwinComparisonError(f"{context} preflight context is invalid")
        TwinComparisonService._digest(item.get("artifact_digest"))
        engine = item.get("engine")
        warnings = item.get("warnings")
        if not isinstance(engine, Mapping) or not isinstance(warnings, list):
            raise TwinComparisonError(f"{context} preflight provenance is incomplete")
        return {
            "request_id": item.get("request_id"),
            "context": context,
            "artifact_digest": item["artifact_digest"],
            "engine": dict(engine),
            "warnings": list(warnings),
            "preflight_verified": True,
        }

    @staticmethod
    def _digest(value: Any) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise TwinComparisonError("input digest must be lowercase SHA-256")
