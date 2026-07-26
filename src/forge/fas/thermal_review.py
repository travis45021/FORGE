"""FAS-030 thermal-management capability design review."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, ClassVar


class ThermalReviewError(ValueError):
    """Raised when thermal review input is incomplete."""


class ThermalDesignReview:
    REQUIRED_ZONE_FIELDS: ClassVar[set[str]] = {
        "zone_id",
        "sensor_id",
        "minimum",
        "maximum",
        "control_mode",
        "max_rate",
        "overtemperature_behavior",
        "sensor_fault_behavior",
        "power_interlock",
    }

    def review(
        self, contract: Mapping[str, Any], *, reviewer: str, reviewed_at: str
    ) -> dict[str, Any]:
        item = deepcopy(dict(contract))
        required = {"capability_id", "version", "provider_id", "zones", "evidence"}
        missing = sorted(required - item.keys())
        if missing:
            raise ThermalReviewError(f"thermal contract missing: {', '.join(missing)}")
        if item["capability_id"] != "thermal.management":
            raise ThermalReviewError(
                "thermal review requires capability_id thermal.management"
            )
        findings: list[str] = []
        ids: set[str] = set()
        if not isinstance(item["zones"], list) or not item["zones"]:
            findings.append("at least one thermal zone is required")
        for zone in item.get("zones", []):
            missing_zone = sorted(self.REQUIRED_ZONE_FIELDS - zone.keys())
            if missing_zone:
                findings.append(
                    f"{zone.get('zone_id', 'unknown')}: missing {', '.join(missing_zone)}"
                )
                continue
            if zone["zone_id"] in ids:
                findings.append(f"duplicate zone: {zone['zone_id']}")
            ids.add(zone["zone_id"])
            if zone["minimum"] >= zone["maximum"] or zone["max_rate"] <= 0:
                findings.append(f"{zone['zone_id']}: invalid thermal limits")
            if zone["control_mode"] not in {"off", "bang_bang", "pid", "manual"}:
                findings.append(f"{zone['zone_id']}: unsupported control mode")
            for field in (
                "overtemperature_behavior",
                "sensor_fault_behavior",
                "power_interlock",
            ):
                if not zone[field]:
                    findings.append(f"{zone['zone_id']}: {field} is required")
        if not isinstance(item["evidence"], list) or not item["evidence"]:
            findings.append("at least one evidence reference is required")
        return {
            "review_id": f"forge-review:{item['provider_id'].split(':')[-1]}:thermal",
            "capability_id": item["capability_id"],
            "provider_id": item["provider_id"],
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "status": "needs_work" if findings else "accepted_for_integration_review",
            "findings": findings,
            "execution_authorized": False,
            "hardware_safety_asserted": False,
        }
