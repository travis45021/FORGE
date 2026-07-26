"""FAS-032 vision and observation capability review."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, ClassVar


class VisionReviewError(ValueError):
    """Raised when vision review input is incomplete."""


class VisionDesignReview:
    REQUIRED_SENSOR_FIELDS: ClassVar[set[str]] = {
        "sensor_id",
        "modality",
        "resolution",
        "rate",
        "privacy_mode",
        "failure_behavior",
    }

    def review(
        self, contract: Mapping[str, Any], *, reviewer: str, reviewed_at: str
    ) -> dict[str, Any]:
        item = deepcopy(dict(contract))
        required = {"capability_id", "version", "provider_id", "sensors", "evidence"}
        missing = sorted(required - item.keys())
        if missing:
            raise VisionReviewError(f"vision contract missing: {', '.join(missing)}")
        if item["capability_id"] != "vision.observation":
            raise VisionReviewError(
                "vision review requires capability_id vision.observation"
            )
        findings: list[str] = []
        ids: set[str] = set()
        if not isinstance(item["sensors"], list) or not item["sensors"]:
            findings.append("at least one observation sensor is required")
        for sensor in item.get("sensors", []):
            missing_sensor = sorted(self.REQUIRED_SENSOR_FIELDS - sensor.keys())
            if missing_sensor:
                findings.append(
                    f"{sensor.get('sensor_id', 'unknown')}: missing {', '.join(missing_sensor)}"
                )
                continue
            if sensor["sensor_id"] in ids:
                findings.append(f"duplicate sensor: {sensor['sensor_id']}")
            ids.add(sensor["sensor_id"])
            if sensor["rate"] <= 0 or not sensor["resolution"]:
                findings.append(
                    f"{sensor['sensor_id']}: resolution and rate are required"
                )
            if sensor["privacy_mode"] not in {
                "local_only",
                "redacted",
                "user_approved",
            }:
                findings.append(f"{sensor['sensor_id']}: invalid privacy mode")
            if not sensor["failure_behavior"]:
                findings.append(f"{sensor['sensor_id']}: failure behavior is required")
        if not isinstance(item["evidence"], list) or not item["evidence"]:
            findings.append("at least one evidence reference is required")
        return {
            "review_id": f"forge-review:{item['provider_id'].split(':')[-1]}:vision",
            "capability_id": item["capability_id"],
            "provider_id": item["provider_id"],
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "status": "needs_work" if findings else "accepted_for_integration_review",
            "findings": findings,
            "execution_authorized": False,
            "hardware_safety_asserted": False,
            "v1_required": False,
        }
