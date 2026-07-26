"""FAS-036 software update, compatibility, and rollback contract."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class UpdateError(ValueError):
    """Raised when an update cannot pass compatibility or rollback gates."""


class UpdateManager:
    """Plan updates without installing or restarting trusted services."""

    def __init__(self) -> None:
        self._updates: dict[str, dict[str, Any]] = {}

    def plan(
        self,
        manifest: Mapping[str, Any],
        *,
        current_version: str,
        approval_reference: str,
    ) -> dict[str, Any]:
        item = deepcopy(dict(manifest))
        required = {
            "update_id",
            "component",
            "version",
            "minimum_runtime",
            "digest",
            "rollback_version",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise UpdateError(f"update manifest missing: {', '.join(missing)}")
        if not approval_reference or item["version"] == current_version:
            raise UpdateError("update requires explicit approval and a version change")
        if not item["digest"].startswith("sha256:"):
            raise UpdateError("update digest must be sha256")
        plan = {
            "update_id": item["update_id"],
            "component": item["component"],
            "from_version": current_version,
            "to_version": item["version"],
            "rollback_version": item["rollback_version"],
            "minimum_runtime": item["minimum_runtime"],
            "digest": item["digest"],
            "approval_reference": approval_reference,
            "status": "planned",
            "install_authorized": False,
            "physical_execution_allowed": False,
        }
        self._updates[item["update_id"]] = plan
        return deepcopy(plan)

    def compatibility(
        self,
        update_id: str,
        *,
        runtime_version: str,
        backup_verified: bool,
        tests_passed: bool,
    ) -> dict[str, Any]:
        plan = self._require(update_id)
        compatible = (
            runtime_version >= plan["minimum_runtime"]
            and backup_verified is True
            and tests_passed is True
        )
        plan["compatibility"] = {
            "runtime": runtime_version,
            "backup_verified": backup_verified,
            "tests_passed": tests_passed,
        }
        plan["status"] = "ready_for_user_install" if compatible else "blocked"
        return deepcopy(plan)

    def rollback(
        self, update_id: str, *, reason: str, user_approved: bool
    ) -> dict[str, Any]:
        plan = self._require(update_id)
        if user_approved is not True or not reason:
            raise UpdateError("rollback requires user approval and a reason")
        plan.update(
            {
                "status": "rollback_planned",
                "rollback_reason": reason,
                "install_authorized": False,
            }
        )
        return deepcopy(plan)

    def _require(self, update_id: str) -> dict[str, Any]:
        try:
            return self._updates[update_id]
        except KeyError as exc:
            raise UpdateError(f"unknown update: {update_id}") from exc
