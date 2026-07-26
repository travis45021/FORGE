"""FAS-037 constitutional v1 release-scope gate."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class ReleaseGateError(ValueError):
    """Raised when release-gate input is malformed."""


REQUIRED_GATES = {
    "constitution",
    "licensing",
    "tests",
    "documentation",
    "four_click",
    "hardware",
    "recovery",
    "packaging",
    "security",
}


class ReleaseGate:
    """Evaluate release evidence; never self-approve or publish a release."""

    def evaluate(
        self, evidence: Mapping[str, Any], *, reviewed_by: str, reviewed_at: str
    ) -> dict[str, Any]:
        item = deepcopy(dict(evidence))
        missing = sorted(REQUIRED_GATES - item.keys())
        if missing:
            raise ReleaseGateError(f"release evidence missing: {', '.join(missing)}")
        if not reviewed_by or not reviewed_at:
            raise ReleaseGateError("release review identity and timestamp are required")
        failed = sorted(name for name in REQUIRED_GATES if item[name] is not True)
        return {
            "release_id": "forge-release:v1.0",
            "reviewed_by": reviewed_by,
            "reviewed_at": reviewed_at,
            "status": "blocked" if failed else "ready_for_final_human_decision",
            "failed_gates": failed,
            "release_authorized": False,
            "physical_execution_authorized": False,
            "future_gated_features_excluded": True,
        }
