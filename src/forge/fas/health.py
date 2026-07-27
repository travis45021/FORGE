"""Evidence-based health, diagnostics, and bounded recovery for FAS-023."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any


class HealthError(ValueError):
    """Raised when a health or recovery contract violates FAS-023."""


HEALTH_STATES = {
    "healthy",
    "unobserved",
    "stale",
    "degraded",
    "unavailable",
    "failed",
    "recovering",
}


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise HealthError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise HealthError(f"invalid timestamp: {value}") from exc


class HealthService:
    """Tracks honest health and authorizes only narrow automatic recovery."""

    def __init__(self) -> None:
        self._reports: dict[str, dict[str, Any]] = {}
        self._dependencies: dict[str, set[str]] = {}
        self._attempts: dict[tuple[str, str], int] = {}
        self._events: list[dict[str, Any]] = []

    def observe(self, report: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(report))
        required = {
            "object_id",
            "state",
            "observed_at",
            "fresh_for_seconds",
            "confidence",
            "check_type",
            "evidence",
            "reason_codes",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise HealthError(f"health report missing fields: {', '.join(missing)}")
        if item["state"] not in HEALTH_STATES:
            raise HealthError("unknown health state")
        _utc(item["observed_at"])
        fresh = item["fresh_for_seconds"]
        if isinstance(fresh, bool) or not isinstance(fresh, int) or fresh < 0:
            raise HealthError("fresh_for_seconds must be a nonnegative integer")
        confidence = item["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise HealthError("confidence must be numeric")
        if not 0 <= confidence <= 1:
            raise HealthError("confidence must be between zero and one")
        if not isinstance(item["evidence"], list) or not item["evidence"]:
            raise HealthError("health conclusions require diagnostic evidence")
        if not isinstance(item["reason_codes"], list) or not item["reason_codes"]:
            raise HealthError("health conclusions require reason codes")
        item.setdefault("affected_capabilities", [])
        item.setdefault("source", "local")
        self._reports[item["object_id"]] = item
        self._record("health.observed", item["object_id"], item["state"])
        return deepcopy(item)

    def evaluate(self, object_id: str, *, evaluated_at: str) -> dict[str, Any]:
        report = deepcopy(self._require(object_id))
        age = (_utc(evaluated_at) - _utc(report["observed_at"])).total_seconds()
        if age > report["fresh_for_seconds"] and report["state"] != "unobserved":
            report["state"] = "stale"
            report["reason_codes"] = ["observation_expired"]
        report["evaluated_at"] = evaluated_at
        report["age_seconds"] = max(0, int(age))
        return report

    def set_dependencies(self, object_id: str, dependencies: list[str]) -> None:
        if len(dependencies) != len(set(dependencies)) or object_id in dependencies:
            raise HealthError(
                "dependencies must be unique and cannot be self-referential"
            )
        self._dependencies[object_id] = set(dependencies)

    def impact(self, failed_object_id: str) -> dict[str, Any]:
        direct = sorted(
            object_id
            for object_id, dependencies in self._dependencies.items()
            if failed_object_id in dependencies
        )
        return {
            "source_object_id": failed_object_id,
            "direct_dependents": direct,
            "isolated_objects": sorted(
                set(self._reports) - set(direct) - {failed_object_id}
            ),
        }

    def diagnose(
        self,
        object_id: str,
        *,
        evidence: list[Mapping[str, Any]],
        hypotheses: list[str] | None = None,
    ) -> dict[str, Any]:
        self._require(object_id)
        if not evidence:
            raise HealthError("diagnostics require evidence")
        return {
            "object_id": object_id,
            "evidence": deepcopy(evidence),
            "hypotheses": [
                {"statement": statement, "status": "unconfirmed"}
                for statement in (hypotheses or [])
            ],
            "cause_confirmed": False,
        }

    def plan_recovery(
        self,
        object_id: str,
        action: Mapping[str, Any],
        *,
        executive_authorized: bool = False,
        safety_verified: bool = False,
    ) -> dict[str, Any]:
        report = self._require(object_id)
        plan = deepcopy(dict(action))
        required = {
            "action_id",
            "scope",
            "deterministic",
            "physical",
            "risk",
            "maximum_attempts",
            "verification_check",
        }
        missing = sorted(required - plan.keys())
        if missing:
            raise HealthError(f"recovery action missing fields: {', '.join(missing)}")
        maximum = plan["maximum_attempts"]
        if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 1:
            raise HealthError("maximum_attempts must be a positive integer")
        key = (object_id, plan["action_id"])
        attempts = self._attempts.get(key, 0)
        physical_allowed = (
            plan["physical"] is True
            and executive_authorized is True
            and safety_verified is True
        )
        automatic = (
            plan["deterministic"] is True
            and plan["physical"] is False
            and plan["risk"] == "low"
        )
        if attempts >= maximum:
            decision, reason = "suppressed", "retry_limit_reached"
        elif report["state"] in {"healthy", "unobserved", "stale"}:
            decision, reason = "suppressed", "recovery_not_indicated"
        elif automatic:
            decision, reason = "approved_automatic", "bounded_low_risk_action"
        elif physical_allowed:
            decision, reason = "approved_manual", "authority_and_safety_verified"
        else:
            decision, reason = "requires_authorization", "outside_v1_automatic_boundary"
        result = {
            **plan,
            "object_id": object_id,
            "decision": decision,
            "reason": reason,
            "attempts": attempts,
            "attempts_remaining": max(0, maximum - attempts),
        }
        self._record("recovery.planned", object_id, reason)
        return result

    def begin_recovery(self, plan: Mapping[str, Any]) -> dict[str, Any]:
        if plan.get("decision") not in {"approved_automatic", "approved_manual"}:
            raise HealthError("recovery plan is not approved")
        object_id = str(plan["object_id"])
        action_id = str(plan["action_id"])
        key = (object_id, action_id)
        self._attempts[key] = self._attempts.get(key, 0) + 1
        report = self._require(object_id)
        report["state"] = "recovering"
        report["reason_codes"] = [f"recovery:{action_id}"]
        self._record("recovery.started", object_id, action_id)
        return {"object_id": object_id, "action_id": action_id, "state": "recovering"}

    def complete_recovery(
        self,
        object_id: str,
        *,
        verified: bool,
        evidence: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        report = self._require(object_id)
        if report["state"] != "recovering":
            raise HealthError("object is not recovering")
        if not evidence:
            raise HealthError("recovery outcome requires verification evidence")
        report["evidence"] = deepcopy(evidence)
        report["state"] = "healthy" if verified else "failed"
        report["reason_codes"] = [
            "recovery_verified" if verified else "recovery_verification_failed"
        ]
        self._record("recovery.completed", object_id, report["state"])
        return deepcopy(report)

    def report(self, object_id: str) -> dict[str, Any] | None:
        value = self._reports.get(object_id)
        return deepcopy(value) if value else None

    def events(self) -> list[dict[str, Any]]:
        return deepcopy(self._events)

    def _require(self, object_id: str) -> dict[str, Any]:
        try:
            return self._reports[object_id]
        except KeyError as exc:
            raise HealthError(f"unknown health object: {object_id}") from exc

    def _record(self, event_type: str, object_id: str, reason: str) -> None:
        self._events.append(
            {"event_type": event_type, "object_id": object_id, "reason": reason}
        )
