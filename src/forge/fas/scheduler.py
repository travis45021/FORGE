"""Deterministic local Mission scheduler for canonical FAS-015."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping


class SchedulingError(ValueError):
    """Raised when scheduling violates FAS-015."""


PRIORITY = {
    "background": 0,
    "low": 1,
    "normal": 2,
    "high": 3,
    "critical": 4,
    "emergency": 5,
}


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise SchedulingError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SchedulingError(f"invalid timestamp: {value}") from exc


class MissionScheduler:
    """Schedules already-authorized Missions; it never commands hardware."""

    def __init__(self, *, ai_enabled: bool = False) -> None:
        self._ai_enabled = ai_enabled
        self._missions: dict[str, dict[str, Any]] = {}
        self._completed: set[str] = set()
        self._resources: dict[str, str] = {}
        self._history: list[dict[str, Any]] = []

    def submit(
        self, mission: Mapping[str, Any], *, executive_authorized: bool
    ) -> dict[str, Any]:
        item = deepcopy(dict(mission))
        self._validate(item)
        if executive_authorized is not True:
            raise SchedulingError("priority is not permission")
        mission_id = item["mission_id"]
        if mission_id in self._missions:
            raise SchedulingError("mission is already scheduled")
        item.update(
            {
                "state": "queued",
                "reason": "authorized_and_queued",
                "attempts": 0,
                "effective_priority": item["priority"],
            }
        )
        self._missions[mission_id] = item
        self._record("mission.queued", mission_id, item["reason"])
        return deepcopy(item)

    def next_ready(
        self,
        *,
        evaluated_at: str,
        conditions: Mapping[str, bool] | None = None,
    ) -> dict[str, Any] | None:
        now = _utc(evaluated_at)
        observed = dict(conditions or {})
        candidates: list[tuple[int, datetime, str, dict[str, Any]]] = []
        for item in self._missions.values():
            if item["state"] not in {
                "queued", "waiting_for_approval", "waiting_for_capability",
                "waiting_for_resource", "waiting_for_condition",
            }:
                continue
            reason = self._blocked_reason(item, observed)
            if reason:
                item["state"], item["reason"] = reason
                continue
            score = self._priority_score(item, now)
            item["effective_priority"] = next(
                name for name, value in PRIORITY.items() if value == score
            )
            candidates.append(
                (-score, _utc(item["queued_at"]), item["mission_id"], item)
            )
        if not candidates:
            return None
        candidates.sort(key=lambda value: value[:3])
        selected = candidates[0][3]
        selected["state"] = "scheduled"
        selected["reason"] = "highest_ready_effective_priority"
        self._record("mission.scheduled", selected["mission_id"], selected["reason"])
        return deepcopy(selected)

    def start(self, mission_id: str) -> dict[str, Any]:
        item = self._require(mission_id)
        if item["state"] != "scheduled":
            raise SchedulingError("mission must be scheduled before start")
        conflicts = [
            resource for resource in item["resources"] if resource in self._resources
        ]
        if conflicts:
            item["state"] = "waiting_for_resource"
            item["reason"] = "resource_conflict:" + ",".join(sorted(conflicts))
            return deepcopy(item)
        for resource in item["resources"]:
            self._resources[resource] = mission_id
        item["state"] = "running"
        item["reason"] = "resources_reserved"
        self._record("mission.started", mission_id, item["reason"])
        return deepcopy(item)

    def preempt(
        self,
        running_id: str,
        incoming_id: str,
        *,
        executive_authorized: bool,
        policy_allows: bool,
    ) -> dict[str, Any]:
        running = self._require(running_id)
        incoming = self._require(incoming_id)
        if running["state"] != "running":
            raise SchedulingError("only running Missions can be preempted")
        if executive_authorized is not True or policy_allows is not True:
            raise SchedulingError("preemption requires authority and policy")
        emergency = incoming["priority"] == "emergency"
        if not emergency and not running["at_safe_pause_point"]:
            raise SchedulingError("preemption requires a safe pause point")
        if not emergency and PRIORITY[incoming["priority"]] <= PRIORITY[
            running["priority"]
        ]:
            raise SchedulingError("preemption requires higher priority")
        for resource in list(self._resources):
            if self._resources[resource] == running_id:
                del self._resources[resource]
        running["state"] = "preempted"
        running["reason"] = f"preempted_by:{incoming_id}"
        self._record("mission.preempted", running_id, running["reason"])
        return deepcopy(running)

    def complete(self, mission_id: str) -> dict[str, Any]:
        item = self._require(mission_id)
        if item["state"] != "running":
            raise SchedulingError("only running Missions can complete")
        for resource in list(self._resources):
            if self._resources[resource] == mission_id:
                del self._resources[resource]
        item["state"] = "completed"
        item["reason"] = "mission_completed"
        self._completed.add(mission_id)
        self._record("mission.completed", mission_id, item["reason"])
        return deepcopy(item)

    def retry(self, mission_id: str) -> dict[str, Any]:
        item = self._require(mission_id)
        item["attempts"] += 1
        if item["attempts"] > item["retry_policy"]["maximum_attempts"]:
            item["state"] = "failed"
            item["reason"] = "retry_limit_reached"
        else:
            item["state"] = "queued"
            item["reason"] = "bounded_retry_queued"
        self._record("mission.retry_evaluated", mission_id, item["reason"])
        return deepcopy(item)

    def approve(self, mission_id: str) -> None:
        self._require(mission_id)["approval_verified"] = True

    def mission(self, mission_id: str) -> dict[str, Any] | None:
        item = self._missions.get(mission_id)
        return deepcopy(item) if item else None

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def health(self) -> dict[str, Any]:
        states: dict[str, int] = {}
        for item in self._missions.values():
            states[item["state"]] = states.get(item["state"], 0) + 1
        return {
            "state": "ready",
            "missions_by_state": states,
            "reserved_resources": len(self._resources),
        }

    def _blocked_reason(
        self, item: Mapping[str, Any], conditions: Mapping[str, bool]
    ) -> tuple[str, str] | None:
        if item["requires_approval"] and not item["approval_verified"]:
            return "waiting_for_approval", "approval_required"
        if item["requires_ai"] and not self._ai_enabled:
            return "waiting_for_capability", "ai_required_but_disabled"
        missing = [dep for dep in item["dependencies"] if dep not in self._completed]
        if missing:
            return "waiting_for_condition", "dependencies_incomplete"
        if any(not conditions.get(name, False) for name in item["conditions"]):
            return "waiting_for_condition", "condition_not_met"
        if any(resource in self._resources for resource in item["resources"]):
            return "waiting_for_resource", "resource_conflict"
        return None

    def _priority_score(self, item: Mapping[str, Any], now: datetime) -> int:
        base = PRIORITY[item["priority"]]
        if base >= PRIORITY["critical"]:
            return base
        age_days = max(0, (now - _utc(item["queued_at"])).days)
        return min(PRIORITY["high"], base + age_days // 7)

    def _validate(self, item: Mapping[str, Any]) -> None:
        required = {
            "mission_id", "priority", "queued_at", "deadline", "resources",
            "dependencies", "conditions", "requires_approval",
            "approval_verified", "requires_ai", "at_safe_pause_point",
            "retry_policy", "cost_limit", "offline_capable",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise SchedulingError(f"mission missing fields: {', '.join(missing)}")
        if item["priority"] not in PRIORITY:
            raise SchedulingError("unknown priority")
        _utc(item["queued_at"])
        if item["deadline"] is not None:
            _utc(item["deadline"])
        for field in ("resources", "dependencies", "conditions"):
            if not isinstance(item[field], list) or len(item[field]) != len(
                set(item[field])
            ):
                raise SchedulingError(f"{field} must be a unique list")
        attempts = item["retry_policy"].get("maximum_attempts")
        if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 0:
            raise SchedulingError("retry maximum must be a nonnegative integer")

    def _require(self, mission_id: str) -> dict[str, Any]:
        try:
            return self._missions[mission_id]
        except KeyError as exc:
            raise SchedulingError(f"unknown mission: {mission_id}") from exc

    def _record(self, event_type: str, mission_id: str, reason: str) -> None:
        self._history.append(
            {"event_type": event_type, "mission_id": mission_id, "reason": reason}
        )
