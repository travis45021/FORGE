"""FAS-036 software update, compatibility, and rollback contract."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class UpdateError(ValueError):
    """Raised when an update cannot pass compatibility or rollback gates."""


def _version(value: str) -> tuple[int, ...]:
    if (
        not isinstance(value, str)
        or not value
        or any(not part.isdigit() for part in value.split("."))
    ):
        raise UpdateError("versions must be numeric dotted values")
    return tuple(int(part) for part in value.split("."))


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
        for field in ("update_id", "component", "version", "rollback_version"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise UpdateError(f"update {field} must be a non-empty string")
        current = _version(current_version)
        target = _version(item["version"])
        rollback = _version(item["rollback_version"])
        _version(item["minimum_runtime"])
        if (
            not isinstance(approval_reference, str)
            or not approval_reference.strip()
            or target == current
        ):
            raise UpdateError("update requires explicit approval and a version change")
        if target <= current or rollback >= target:
            raise UpdateError("update versions must advance and have an older rollback")
        if (
            not isinstance(item["digest"], str)
            or len(item["digest"]) != 71
            or not item["digest"].startswith("sha256:")
            or any(
                character not in "0123456789abcdef" for character in item["digest"][7:]
            )
        ):
            raise UpdateError("update digest must be sha256")
        plan = {
            "update_id": item["update_id"],
            "component": item["component"],
            "from_version": current_version,
            "to_version": item["version"],
            "rollback_version": item["rollback_version"],
            "minimum_runtime": item["minimum_runtime"],
            "digest": item["digest"],
            "approval_reference": approval_reference.strip(),
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
            _version(runtime_version) >= _version(plan["minimum_runtime"])
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
