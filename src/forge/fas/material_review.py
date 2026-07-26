"""FAS-031 material-handling and extrusion capability review."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, ClassVar


class MaterialReviewError(ValueError):
    """Raised when material capability review input is incomplete."""


class MaterialDesignReview:
    REQUIRED_FIELDS: ClassVar[set[str]] = {
        "material_id",
        "feed_min",
        "feed_max",
        "max_feed_rate",
        "max_extrusion_rate",
        "retraction_supported",
        "jam_behavior",
        "sensor_fault_behavior",
        "temperature_reference",
    }

    def review(
        self, contract: Mapping[str, Any], *, reviewer: str, reviewed_at: str
    ) -> dict[str, Any]:
        item = deepcopy(dict(contract))
        required = {"capability_id", "version", "provider_id", "materials", "evidence"}
        missing = sorted(required - item.keys())
        if missing:
            raise MaterialReviewError(
                f"material contract missing: {', '.join(missing)}"
            )
        if item["capability_id"] != "material.handling":
            raise MaterialReviewError(
                "material review requires capability_id material.handling"
            )
        findings: list[str] = []
        ids: set[str] = set()
        if not isinstance(item["materials"], list) or not item["materials"]:
            findings.append("at least one material profile is required")
        for material in item.get("materials", []):
            missing_material = sorted(self.REQUIRED_FIELDS - material.keys())
            if missing_material:
                findings.append(
                    f"{material.get('material_id', 'unknown')}: missing {', '.join(missing_material)}"
                )
                continue
            if material["material_id"] in ids:
                findings.append(f"duplicate material: {material['material_id']}")
            ids.add(material["material_id"])
            if (
                material["feed_min"] >= material["feed_max"]
                or material["max_feed_rate"] <= 0
                or material["max_extrusion_rate"] <= 0
            ):
                findings.append(
                    f"{material['material_id']}: invalid feed or extrusion limits"
                )
            for field in (
                "jam_behavior",
                "sensor_fault_behavior",
                "temperature_reference",
            ):
                if not material[field]:
                    findings.append(f"{material['material_id']}: {field} is required")
        if not isinstance(item["evidence"], list) or not item["evidence"]:
            findings.append("at least one evidence reference is required")
        return {
            "review_id": f"forge-review:{item['provider_id'].split(':')[-1]}:material",
            "capability_id": item["capability_id"],
            "provider_id": item["provider_id"],
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "status": "needs_work" if findings else "accepted_for_integration_review",
            "findings": findings,
            "execution_authorized": False,
            "hardware_safety_asserted": False,
        }
