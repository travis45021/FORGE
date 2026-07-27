"""Deterministic interaction and attention controls for canonical FAS-012."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, time
from typing import Any


class InteractionError(ValueError):
    """Raised when an interaction violates FAS-012."""


INTERACTION_CLASSES = {
    "status",
    "information",
    "suggestion",
    "approval_request",
    "warning",
    "critical_alert",
    "outcome",
}

PROFILE_DEFAULTS = {
    "quiet": {
        "ai_enabled": False,
        "suggestions_enabled": False,
        "maximum_suggestions_per_day": 0,
        "maximum_suggestions_per_mission": 0,
    },
    "simple": {
        "ai_enabled": False,
        "suggestions_enabled": False,
        "maximum_suggestions_per_day": 0,
        "maximum_suggestions_per_mission": 0,
    },
    "guided": {
        "ai_enabled": False,
        "suggestions_enabled": True,
        "maximum_suggestions_per_day": 2,
        "maximum_suggestions_per_mission": 1,
    },
    "proactive": {
        "ai_enabled": True,
        "suggestions_enabled": True,
        "maximum_suggestions_per_day": 4,
        "maximum_suggestions_per_mission": 2,
    },
    "managed": {
        "ai_enabled": False,
        "suggestions_enabled": False,
        "maximum_suggestions_per_day": 0,
        "maximum_suggestions_per_mission": 0,
    },
}

ESSENTIAL_CLASSES = {"approval_request", "warning", "critical_alert"}
QUIET_HOUR_EXEMPT = {"approval_request", "critical_alert"}


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InteractionError("interaction value must be canonical JSON") from exc


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise InteractionError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise InteractionError(f"invalid timestamp: {value}") from exc


def _clock(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise InteractionError("quiet-hour times must use HH:MM") from exc


def _digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


class InteractionManager:
    """In-memory reference manager for user intent and attention."""

    def __init__(self, preferences: Mapping[str, Any] | None = None) -> None:
        self._preferences = self._normalize_preferences(preferences)
        self._presented: list[dict[str, Any]] = []
        self._active_deduplication_keys: set[str] = set()
        self._dismissals: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def preferences(self) -> dict[str, Any]:
        return deepcopy(self._preferences)

    def update_preferences(self, changes: Mapping[str, Any]) -> dict[str, Any]:
        """Update communication choices without changing automation authority."""
        candidate = deepcopy(self._preferences)
        if (
            "automation_profile" in changes
            and changes["automation_profile"] != candidate["automation_profile"]
        ):
            raise InteractionError(
                "interaction preferences cannot change automation authority"
            )
        candidate.update(deepcopy(dict(changes)))
        self._preferences = self._normalize_preferences(candidate)
        self._record("interaction.profile.changed", self._preferences)
        return self.preferences()

    def reset_preferences(self) -> dict[str, Any]:
        automation_profile = self._preferences["automation_profile"]
        self._preferences = self._normalize_preferences(
            {"automation_profile": automation_profile}
        )
        self._dismissals.clear()
        self._record("interaction.preferences.reset", self._preferences)
        return self.preferences()

    def classify_delivery(
        self,
        interaction_class: str,
        *,
        evaluated_at: str,
        requested: bool = False,
    ) -> dict[str, Any]:
        """Decide whether a user-facing interaction may interrupt now."""
        if interaction_class not in INTERACTION_CLASSES:
            raise InteractionError("unknown interaction class")
        _utc(evaluated_at)
        if interaction_class == "suggestion":
            if requested:
                return self._decision("deliver", "user_requested")
            if not self._preferences["suggestions_enabled"]:
                return self._decision("suppress", "suggestions_disabled")
        if (
            self._preferences["interaction_profile"] == "quiet"
            and interaction_class not in ESSENTIAL_CLASSES
            and not requested
        ):
            return self._decision("defer", "quiet_profile")
        if (
            self._in_quiet_hours(evaluated_at)
            and interaction_class not in QUIET_HOUR_EXEMPT
            and not requested
        ):
            return self._decision("defer", "quiet_hours")
        return self._decision("deliver", "allowed_by_interaction_policy")

    def evaluate_suggestion(
        self,
        suggestion: Mapping[str, Any],
        *,
        evaluated_at: str,
        mission_id: str | None = None,
        requested: bool = False,
    ) -> dict[str, Any]:
        """Evaluate suggestion eligibility, repetition, and attention budget."""
        item = deepcopy(dict(suggestion))
        self._validate_suggestion(item)
        when = _utc(evaluated_at)
        if item["source_type"] == "ai" and not self._preferences["ai_enabled"]:
            return self._decision("suppress", "ai_disabled")
        if (
            item["category"] in self._preferences["disabled_categories"]
            and not requested
        ):
            return self._decision("suppress", "category_disabled")

        dismissal = self._dismissals.get(item["deduplication_key"])
        if dismissal and not requested:
            if dismissal["mode"] == "permanent":
                if dismissal["evidence_digest"] == item["evidence_digest"]:
                    return self._decision("suppress", "permanently_dismissed")
            elif when < _utc(dismissal["remind_at"]):
                return self._decision("suppress", "dismissal_cooldown")

        if (
            item["deduplication_key"] in self._active_deduplication_keys
            and not requested
        ):
            return self._decision("suppress", "duplicate_active_suggestion")

        delivery = self.classify_delivery(
            "suggestion", evaluated_at=evaluated_at, requested=requested
        )
        if delivery["disposition"] != "deliver":
            return delivery
        if not requested and self._budget_exhausted(when, mission_id):
            return self._decision("defer", "suggestion_budget_exhausted")

        presentation = {
            "suggestion_id": item["suggestion_id"],
            "deduplication_key": item["deduplication_key"],
            "evidence_digest": item["evidence_digest"],
            "presented_at": evaluated_at,
            "mission_id": mission_id,
            "requested": requested,
        }
        self._presented.append(presentation)
        self._active_deduplication_keys.add(item["deduplication_key"])
        self._record("suggestion.presented", presentation)
        return {
            **self._decision("deliver", "eligible"),
            "suggestion_id": item["suggestion_id"],
        }

    def dismiss_suggestion(
        self,
        suggestion: Mapping[str, Any],
        *,
        mode: str,
        remind_at: str | None = None,
    ) -> dict[str, Any]:
        item = deepcopy(dict(suggestion))
        self._validate_suggestion(item)
        if mode not in {"permanent", "remind_later"}:
            raise InteractionError("invalid dismissal mode")
        if mode == "remind_later":
            if remind_at is None:
                raise InteractionError("remind_later requires remind_at")
            _utc(remind_at)
        record = {
            "mode": mode,
            "evidence_digest": item["evidence_digest"],
            "remind_at": remind_at,
        }
        self._dismissals[item["deduplication_key"]] = record
        self._active_deduplication_keys.discard(item["deduplication_key"])
        self._record(
            "suggestion.dismissed",
            {"deduplication_key": item["deduplication_key"], **record},
        )
        return deepcopy(record)

    def resolve_suggestion(self, deduplication_key: str) -> None:
        self._active_deduplication_keys.discard(deduplication_key)

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def _normalize_preferences(
        self, preferences: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        supplied = deepcopy(dict(preferences or {}))
        profile = supplied.get("interaction_profile", "simple")
        if profile not in PROFILE_DEFAULTS:
            raise InteractionError("unknown interaction profile")
        result = {
            "schema_version": "1.0.0",
            "interaction_profile": profile,
            **PROFILE_DEFAULTS[profile],
            "automation_profile": "manual",
            "disabled_categories": [],
            "quiet_hours": None,
            **supplied,
        }
        if not isinstance(result["ai_enabled"], bool):
            raise InteractionError("ai_enabled must be boolean")
        if not isinstance(result["suggestions_enabled"], bool):
            raise InteractionError("suggestions_enabled must be boolean")
        for field in (
            "maximum_suggestions_per_day",
            "maximum_suggestions_per_mission",
        ):
            if isinstance(result[field], bool) or not isinstance(result[field], int):
                raise InteractionError(f"{field} must be an integer")
            if not 0 <= result[field] <= 100:
                raise InteractionError(f"{field} is outside supported bounds")
        categories = result["disabled_categories"]
        if not isinstance(categories, list) or len(categories) != len(set(categories)):
            raise InteractionError("disabled categories must be a unique list")
        quiet_hours = result["quiet_hours"]
        if quiet_hours is not None:
            if set(quiet_hours) != {"start", "end"}:
                raise InteractionError("quiet_hours requires start and end")
            _clock(quiet_hours["start"])
            _clock(quiet_hours["end"])
        return result

    def _validate_suggestion(self, item: Mapping[str, Any]) -> None:
        required = {
            "suggestion_id",
            "category",
            "source_type",
            "subject_id",
            "summary",
            "evidence_refs",
            "evidence_digest",
            "expected_benefit",
            "confidence",
            "urgency",
            "interrupt",
            "deduplication_key",
            "actions",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise InteractionError(f"suggestion missing fields: {', '.join(missing)}")
        if item["source_type"] not in {
            "deterministic",
            "ai",
            "user_rule",
            "shared_knowledge",
        }:
            raise InteractionError("invalid suggestion source")
        confidence = item["confidence"]
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            raise InteractionError("confidence must be between zero and one")
        if item["interrupt"] is not False:
            raise InteractionError("ordinary suggestions cannot force interruption")
        if not item["evidence_refs"] or not item["actions"]:
            raise InteractionError("suggestions require evidence and actions")

    def _budget_exhausted(self, when: datetime, mission_id: str | None) -> bool:
        ordinary = [item for item in self._presented if not item["requested"]]
        day_count = sum(
            _utc(item["presented_at"]).date() == when.date() for item in ordinary
        )
        if day_count >= self._preferences["maximum_suggestions_per_day"]:
            return True
        if mission_id is not None:
            mission_count = sum(item["mission_id"] == mission_id for item in ordinary)
            if mission_count >= self._preferences["maximum_suggestions_per_mission"]:
                return True
        return False

    def _in_quiet_hours(self, evaluated_at: str) -> bool:
        window = self._preferences["quiet_hours"]
        if window is None:
            return False
        now = _utc(evaluated_at).time().replace(tzinfo=None)
        start = _clock(window["start"])
        end = _clock(window["end"])
        if start == end:
            return True
        if start < end:
            return start <= now < end
        return now >= start or now < end

    @staticmethod
    def _decision(disposition: str, reason: str) -> dict[str, str]:
        return {"disposition": disposition, "reason_code": reason}

    def _record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        self._history.append(
            {
                "event_type": event_type,
                "payload_digest": _digest(payload),
                "payload": deepcopy(dict(payload)),
            }
        )
