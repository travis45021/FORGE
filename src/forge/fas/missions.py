"""FAS-004 mission lifecycle enforcement."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class MissionTransitionError(ValueError):
    """Raised when a mission transition violates the lifecycle."""


_TRANSITIONS = {
    "created": {"validated", "cancelled"},
    "validated": {"planned", "failed", "cancelled"},
    "planned": {"waiting", "approved", "failed", "cancelled"},
    "waiting": {"approved", "cancelled", "suspended"},
    "approved": {"executing", "cancelled", "suspended"},
    "executing": {"monitoring", "paused", "recovering", "failed", "aborted"},
    "monitoring": {"completed", "paused", "recovering", "failed", "aborted"},
    "paused": {"executing", "recovering", "cancelled", "aborted"},
    "recovering": {"executing", "monitoring", "failed", "aborted"},
    "suspended": {"waiting", "approved", "cancelled"},
    "completed": {"verified", "failed"},
    "verified": {"archived"},
    "cancelled": {"archived"},
    "failed": {"recovering", "archived"},
    "aborted": {"archived"},
    "archived": set(),
}


class MissionLifecycle:
    """Apply explicit mission transitions and emit an event payload."""

    def transition(
        self,
        mission: Mapping[str, Any],
        target: str,
        *,
        actor_id: str,
        reason: str,
        event_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        current = str(mission["state"])
        if target not in _TRANSITIONS.get(current, set()):
            raise MissionTransitionError(f"transition not allowed: {current} -> {target}")
        if not actor_id or not reason or not event_id:
            raise MissionTransitionError("actor, reason, and event are required")
        updated = deepcopy(dict(mission))
        updated["state"] = target
        updated["revision"] = int(updated.get("revision", 0)) + 1
        event = {
            "event_type": "forge.mission.state_changed",
            "event_id": event_id,
            "subject": updated["mission_id"],
            "correlation_id": updated["correlation_id"],
            "payload": {
                "from": current,
                "to": target,
                "actor_id": actor_id,
                "reason": reason,
                "revision": updated["revision"],
            },
        }
        return updated, event
