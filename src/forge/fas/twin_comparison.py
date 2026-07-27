"""Production/twin comparison evidence without authorization power."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .slicing import SlicerContractBoundary, SlicerContractError


class TwinComparisonError(ValueError):
    """Raised when production and twin evidence cannot be safely compared."""


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

    @staticmethod
    def _digest(value: Any) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise TwinComparisonError("input digest must be lowercase SHA-256")
