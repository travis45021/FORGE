"""FAS-035 environment, power, and safety-sensor review."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any, ClassVar


class SafetyReviewError(ValueError):
    """Raised when a safety capability review is incomplete."""


class SafetyDesignReview:
    REQUIRED_FIELDS: ClassVar[set[str]] = {
        "sensor_id",
        "kind",
        "normal_range",
        "trip_behavior",
        "loss_behavior",
        "independent_path",
    }

    def review(
        self, contract: Mapping[str, Any], *, reviewer: str, reviewed_at: str
    ) -> dict[str, Any]:
        item = deepcopy(dict(contract))
        required = {"capability_id", "version", "provider_id", "sensors", "evidence"}
        missing = sorted(required - item.keys())
        if missing:
            raise SafetyReviewError(f"safety contract missing: {', '.join(missing)}")
        if item["capability_id"] != "environment.safety":
            raise SafetyReviewError(
                "safety review requires capability_id environment.safety"
            )
        findings: list[str] = []
        ids: set[str] = set()
        if not isinstance(item["sensors"], list) or not item["sensors"]:
            findings.append("at least one safety sensor is required")
        if not isinstance(item["provider_id"], str) or not item["provider_id"].strip():
            raise SafetyReviewError("safety contract provider identity is invalid")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise SafetyReviewError("safety review requires a reviewer")
        if not isinstance(reviewed_at, str) or not reviewed_at.endswith("Z"):
            raise SafetyReviewError("safety review time must be UTC")
        try:
            datetime.fromisoformat(reviewed_at[:-1] + "+00:00")
        except ValueError as exc:
            raise SafetyReviewError("safety review time must be valid UTC") from exc
        for sensor in item.get("sensors", []):
            if not isinstance(sensor, Mapping):
                findings.append("safety sensor entry must be an object")
                continue
            missing_sensor = sorted(self.REQUIRED_FIELDS - sensor.keys())
            if missing_sensor:
                findings.append(
                    f"{sensor.get('sensor_id', 'unknown')}: missing {', '.join(missing_sensor)}"
                )
                continue
            if sensor["sensor_id"] in ids:
                findings.append(f"duplicate sensor: {sensor['sensor_id']}")
            ids.add(sensor["sensor_id"])
            if (
                not sensor["normal_range"]
                or not sensor["trip_behavior"]
                or not sensor["loss_behavior"]
            ):
                findings.append(
                    f"{sensor['sensor_id']}: range and fail-safe behavior are required"
                )
            if sensor["independent_path"] is not True:
                findings.append(
                    f"{sensor['sensor_id']}: independent safety path is required"
                )
        if not isinstance(item["evidence"], list) or not item["evidence"]:
            findings.append("at least one evidence reference is required")
        return {
            "review_id": f"forge-review:{item['provider_id'].split(':')[-1]}:safety",
            "capability_id": item["capability_id"],
            "provider_id": item["provider_id"],
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "status": "needs_work" if findings else "accepted_for_integration_review",
            "findings": findings,
            "execution_authorized": False,
            "hardware_safety_asserted": False,
        }
