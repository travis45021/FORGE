"""FAS-029 motion and positioning capability design review."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, ClassVar


class DesignReviewError(ValueError):
    """Raised when a capability review input is incomplete."""


class MotionDesignReview:
    """Evaluate motion contracts without approving hardware execution."""

    REQUIRED_AXIS_FIELDS: ClassVar[set[str]] = {
        "axis_id",
        "unit",
        "minimum",
        "maximum",
        "max_velocity",
        "max_acceleration",
        "homing_required",
        "limit_behavior",
        "fault_behavior",
    }

    def review(
        self, contract: Mapping[str, Any], *, reviewer: str, reviewed_at: str
    ) -> dict[str, Any]:
        item = deepcopy(dict(contract))
        required = {"capability_id", "version", "provider_id", "axes", "evidence"}
        missing = sorted(required - item.keys())
        if missing:
            raise DesignReviewError(f"motion contract missing: {', '.join(missing)}")
        if item["capability_id"] != "motion.positioning":
            raise DesignReviewError(
                "motion review requires capability_id motion.positioning"
            )
        if not item["axes"] or not isinstance(item["axes"], list):
            raise DesignReviewError("motion contract requires at least one axis")
        findings: list[str] = []
        ids: set[str] = set()
        for axis in item["axes"]:
            missing_axis = sorted(self.REQUIRED_AXIS_FIELDS - axis.keys())
            if missing_axis:
                findings.append(
                    f"{axis.get('axis_id', 'unknown')}: missing {', '.join(missing_axis)}"
                )
                continue
            if axis["axis_id"] in ids:
                findings.append(f"duplicate axis: {axis['axis_id']}")
            ids.add(axis["axis_id"])
            if axis["minimum"] >= axis["maximum"]:
                findings.append(f"{axis['axis_id']}: minimum must be below maximum")
            if axis["max_velocity"] <= 0 or axis["max_acceleration"] <= 0:
                findings.append(f"{axis['axis_id']}: motion limits must be positive")
            if axis["unit"] not in {"mm", "degree"}:
                findings.append(f"{axis['axis_id']}: unsupported unit")
            if (
                not axis["homing_required"]
                or not axis["limit_behavior"]
                or not axis["fault_behavior"]
            ):
                findings.append(
                    f"{axis['axis_id']}: homing, limits, and fault behavior are required"
                )
        if not isinstance(item["evidence"], list) or not item["evidence"]:
            findings.append("at least one evidence reference is required")
        return {
            "review_id": f"forge-review:{item['provider_id'].split(':')[-1]}:motion",
            "capability_id": item["capability_id"],
            "provider_id": item["provider_id"],
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "status": "needs_work" if findings else "accepted_for_integration_review",
            "findings": findings,
            "execution_authorized": False,
            "hardware_safety_asserted": False,
        }
