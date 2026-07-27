"""Evidence-backed local knowledge core for canonical FAS-013."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any


class KnowledgeError(ValueError):
    """Raised when knowledge violates FAS-013."""


TYPES = {
    "observed_data",
    "evidence",
    "fact",
    "user_statement",
    "measurement",
    "inference",
    "prediction",
    "preference",
    "policy_reference",
    "outcome",
    "unknown",
}
STATES = {
    "provisional",
    "active",
    "stale",
    "disputed",
    "superseded",
    "retired",
    "invalidated",
    "advisory",
}


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise KnowledgeError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise KnowledgeError(f"invalid timestamp: {value}") from exc


class KnowledgeCore:
    """In-memory reference store; informs decisions but grants no authority."""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def create(self, item: Mapping[str, Any]) -> dict[str, Any]:
        candidate = deepcopy(dict(item))
        self._validate(candidate)
        knowledge_id = candidate["knowledge_id"]
        if knowledge_id in self._items:
            raise KnowledgeError("knowledge identifiers are immutable")
        if candidate["origin"] == "shared" and candidate["status"] == "active":
            raise KnowledgeError("shared knowledge is advisory until adopted")
        if candidate["source_class"] == "ai" and (
            candidate["knowledge_type"] not in {"inference", "prediction"}
            or candidate["status"] != "provisional"
            or candidate["requires_verification"] is not True
        ):
            raise KnowledgeError("AI knowledge must remain provisional")
        self._items[knowledge_id] = candidate
        self._record("knowledge.created", knowledge_id, candidate["reason"])
        return deepcopy(candidate)

    def adopt_shared(
        self, knowledge_id: str, *, adopted_by: str, adopted_at: str
    ) -> dict[str, Any]:
        source = self._require(knowledge_id)
        if source["origin"] != "shared":
            raise KnowledgeError("only shared knowledge requires adoption")
        _utc(adopted_at)
        adopted = deepcopy(source)
        adopted["knowledge_id"] = f"{knowledge_id}:local-adoption"
        adopted["origin"] = "local"
        adopted["status"] = "provisional"
        adopted["source_class"] = "user_confirmation"
        adopted["source_refs"] = [knowledge_id, adopted_by]
        adopted["created_at"] = adopted_at
        adopted["updated_at"] = adopted_at
        adopted["last_verified_at"] = None
        adopted["requires_verification"] = True
        adopted["reason"] = "explicit_shared_knowledge_adoption"
        return self.create(adopted)

    def correct(
        self,
        knowledge_id: str,
        *,
        corrected_id: str,
        value: Any,
        corrected_by: str,
        corrected_at: str,
        reason: str,
    ) -> dict[str, Any]:
        prior = self._require(knowledge_id)
        _utc(corrected_at)
        if prior["status"] in {"superseded", "invalidated", "retired"}:
            raise KnowledgeError("inactive knowledge cannot be corrected")
        corrected = deepcopy(prior)
        corrected.update(
            {
                "knowledge_id": corrected_id,
                "value": deepcopy(value),
                "origin": "local",
                "source_class": "user_confirmation",
                "source_refs": [knowledge_id, corrected_by],
                "created_at": corrected_at,
                "updated_at": corrected_at,
                "last_verified_at": corrected_at,
                "status": "active",
                "confidence": 1.0,
                "requires_verification": False,
                "supersedes": knowledge_id,
                "reason": reason,
            }
        )
        result = self.create(corrected)
        prior["status"] = "superseded"
        prior["superseded_by"] = corrected_id
        prior["updated_at"] = corrected_at
        prior["reason"] = reason
        self._record("knowledge.superseded", knowledge_id, reason)
        self.invalidate_dependents(
            knowledge_id, changed_at=corrected_at, reason="dependency_corrected"
        )
        return result

    def invalidate_dependents(
        self, knowledge_id: str, *, changed_at: str, reason: str
    ) -> list[str]:
        _utc(changed_at)
        changed: list[str] = []
        for item in self._items.values():
            if knowledge_id in item["depends_on"] and item["status"] in {
                "active",
                "provisional",
            }:
                item["status"] = "stale"
                item["updated_at"] = changed_at
                item["reason"] = reason
                changed.append(item["knowledge_id"])
                self._record(
                    "knowledge.verification.required", item["knowledge_id"], reason
                )
        return changed

    def item(self, knowledge_id: str) -> dict[str, Any] | None:
        item = self._items.get(knowledge_id)
        return deepcopy(item) if item else None

    def query(
        self, *, subject_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        return [
            deepcopy(item)
            for item in self._items.values()
            if (subject_id is None or item["subject_id"] == subject_id)
            and (status is None or item["status"] == status)
        ]

    def explain(self, knowledge_id: str) -> dict[str, Any]:
        item = self._require(knowledge_id)
        return {
            "knowledge_id": knowledge_id,
            "claim": {
                "subject_id": item["subject_id"],
                "predicate": item["predicate"],
                "value": deepcopy(item["value"]),
            },
            "status": item["status"],
            "confidence": item["confidence"],
            "source_class": item["source_class"],
            "source_refs": deepcopy(item["source_refs"]),
            "depends_on": deepcopy(item["depends_on"]),
            "reason": item["reason"],
            "requires_verification": item["requires_verification"],
        }

    def export(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "items": [deepcopy(self._items[key]) for key in sorted(self._items)],
            "history": deepcopy(self._history),
        }

    def _require(self, knowledge_id: str) -> dict[str, Any]:
        try:
            return self._items[knowledge_id]
        except KeyError as exc:
            raise KnowledgeError(f"unknown knowledge: {knowledge_id}") from exc

    def _validate(self, item: Mapping[str, Any]) -> None:
        required = {
            "knowledge_id",
            "knowledge_type",
            "subject_id",
            "predicate",
            "value",
            "scope",
            "confidence",
            "source_class",
            "source_refs",
            "origin",
            "created_at",
            "updated_at",
            "last_verified_at",
            "expires_at",
            "status",
            "requires_verification",
            "depends_on",
            "supersedes",
            "superseded_by",
            "reason",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise KnowledgeError(f"knowledge missing fields: {', '.join(missing)}")
        if item["knowledge_type"] not in TYPES or item["status"] not in STATES:
            raise KnowledgeError("invalid knowledge type or status")
        if item["origin"] not in {"local", "shared", "imported"}:
            raise KnowledgeError("invalid knowledge origin")
        confidence = item["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise KnowledgeError("confidence must be numeric")
        if not 0 <= confidence <= 1:
            raise KnowledgeError("confidence must be between zero and one")
        if not item["source_refs"]:
            raise KnowledgeError("knowledge requires provenance")
        _utc(item["created_at"])
        _utc(item["updated_at"])
        for field in ("last_verified_at", "expires_at"):
            if item[field] is not None:
                _utc(item[field])
        if not isinstance(item["requires_verification"], bool):
            raise KnowledgeError("requires_verification must be boolean")
        try:
            json.dumps(item["value"], allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise KnowledgeError("knowledge value must be JSON-compatible") from exc

    def _record(self, event_type: str, knowledge_id: str, reason: str) -> None:
        self._history.append(
            {"event_type": event_type, "knowledge_id": knowledge_id, "reason": reason}
        )
