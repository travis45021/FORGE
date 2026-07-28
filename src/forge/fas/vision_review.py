"""FAS-032 vision and observation capability review."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
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
        if not isinstance(item["provider_id"], str) or not item["provider_id"].strip():
            raise VisionReviewError("vision contract provider identity is invalid")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise VisionReviewError("vision review requires a reviewer")
        if not isinstance(reviewed_at, str) or not reviewed_at.endswith("Z"):
            raise VisionReviewError("vision review time must be UTC")
        try:
            datetime.fromisoformat(reviewed_at[:-1] + "+00:00")
        except ValueError as exc:
            raise VisionReviewError("vision review time must be valid UTC") from exc
        for sensor in item.get("sensors", []):
            if not isinstance(sensor, Mapping):
                findings.append("observation sensor entry must be an object")
                continue
            missing_sensor = sorted(self.REQUIRED_SENSOR_FIELDS - sensor.keys())
            if missing_sensor:
                findings.append(
                    f"{sensor.get('sensor_id', 'unknown')}: missing {', '.join(missing_sensor)}"
                )
                continue
            if (
                not isinstance(sensor["sensor_id"], str)
                or not sensor["sensor_id"].strip()
            ):
                findings.append("sensor identity must be non-empty text")
                continue
            if sensor["sensor_id"] in ids:
                findings.append(f"duplicate sensor: {sensor['sensor_id']}")
            ids.add(sensor["sensor_id"])
            if not isinstance(sensor["rate"], (int, float)) or isinstance(
                sensor["rate"], bool
            ):
                findings.append(f"{sensor['sensor_id']}: rate must be numeric")
                continue
            if (
                sensor["rate"] <= 0
                or not isinstance(sensor["resolution"], str)
                or not sensor["resolution"].strip()
            ):
                findings.append(
                    f"{sensor['sensor_id']}: resolution and rate are required"
                )
            if sensor["privacy_mode"] not in {
                "local_only",
                "redacted",
                "user_approved",
            }:
                findings.append(f"{sensor['sensor_id']}: invalid privacy mode")
            if (
                not isinstance(sensor["failure_behavior"], str)
                or not sensor["failure_behavior"].strip()
            ):
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
