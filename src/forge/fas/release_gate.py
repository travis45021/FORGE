"""FAS-037 constitutional v1 release-scope gate."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
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


def _utc(value: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ReleaseGateError("release review timestamp must be UTC and end in Z")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ReleaseGateError("release review timestamp is invalid") from exc


def _digest(value: Mapping[str, bool]) -> str:
    encoded = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class ReleaseGate:
    """Evaluate release evidence; never self-approve or publish a release."""

    def evaluate(
        self, evidence: Mapping[str, Any], *, reviewed_by: str, reviewed_at: str
    ) -> dict[str, Any]:
        item = deepcopy(dict(evidence))
        missing = sorted(REQUIRED_GATES - item.keys())
        if missing:
            raise ReleaseGateError(f"release evidence missing: {', '.join(missing)}")
        unexpected = sorted(item.keys() - REQUIRED_GATES)
        if unexpected:
            raise ReleaseGateError(f"unknown release evidence: {', '.join(unexpected)}")
        if any(type(item[name]) is not bool for name in REQUIRED_GATES):
            raise ReleaseGateError("release evidence values must be explicit booleans")
        if not isinstance(reviewed_by, str) or not reviewed_by.strip():
            raise ReleaseGateError("release review identity and timestamp are required")
        _utc(reviewed_at)
        failed = sorted(name for name in REQUIRED_GATES if item[name] is not True)
        ordered_evidence = {name: item[name] for name in sorted(REQUIRED_GATES)}
        return {
            "schema_version": "1.0.0",
            "release_id": "forge-release:v1.0",
            "reviewed_by": reviewed_by.strip(),
            "reviewed_at": reviewed_at,
            "evidence": ordered_evidence,
            "evidence_digest": _digest(ordered_evidence),
            "status": "blocked" if failed else "ready_for_final_human_decision",
            "failed_gates": failed,
            "release_authorized": False,
            "physical_execution_authorized": False,
            "future_gated_features_excluded": True,
        }
