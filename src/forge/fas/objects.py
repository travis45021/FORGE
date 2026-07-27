"""Typed object graph and Operational Twin v0.1 for canonical FAS-019."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any


class ObjectSystemError(ValueError):
    """Raised when an object or relationship violates FAS-019."""


LIFECYCLE = {
    "declared",
    "discovered",
    "configured",
    "provisional",
    "validated",
    "active",
    "degraded",
    "unavailable",
    "retired",
}
KNOWLEDGE_STATES = {
    "unknown",
    "user_declared",
    "detected_unverified",
    "locally_measured",
    "validated",
    "conflicting",
    "expired",
}
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
        raise ObjectSystemError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ObjectSystemError(f"invalid timestamp: {value}") from exc


class ObjectSystem:
    """Versioned local object graph; not a physics simulator or authority."""

    def __init__(self) -> None:
        self._objects: dict[str, dict[str, Any]] = {}
        self._versions: dict[str, list[dict[str, Any]]] = {}
        self._relationships: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def create(self, object_record: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(object_record))
        self._validate_object(item)
        object_id = item["object_id"]
        if object_id in self._objects:
            raise ObjectSystemError("object identity is immutable")
        self._objects[object_id] = item
        self._versions[object_id] = [deepcopy(item)]
        self._record("object.declared", object_id, item["reason"])
        return deepcopy(item)

    def update(
        self,
        object_id: str,
        changes: Mapping[str, Any],
        *,
        updated_at: str,
        reason: str,
        evidence_refs: list[str],
    ) -> dict[str, Any]:
        current = self._require(object_id)
        _utc(updated_at)
        if "object_id" in changes and changes["object_id"] != object_id:
            raise ObjectSystemError("object identity cannot change")
        if not evidence_refs:
            raise ObjectSystemError("object changes require evidence")
        candidate = deepcopy(current)
        candidate.update(deepcopy(dict(changes)))
        candidate["version"] = current["version"] + 1
        candidate["updated_at"] = updated_at
        candidate["evidence_refs"] = list(
            dict.fromkeys(current["evidence_refs"] + evidence_refs)
        )
        candidate["reason"] = reason
        self._validate_object(candidate)
        self._objects[object_id] = candidate
        self._versions[object_id].append(deepcopy(candidate))
        self._record("object.updated", object_id, reason)
        return deepcopy(candidate)

    def add_relationship(self, relationship: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(relationship))
        required = {
            "relationship_id",
            "source_id",
            "relationship_type",
            "target_id",
            "scope",
            "knowledge_state",
            "evidence_refs",
            "created_at",
            "active",
            "reason",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise ObjectSystemError(
                f"relationship missing fields: {', '.join(missing)}"
            )
        if item["relationship_id"] in self._relationships:
            raise ObjectSystemError("relationship identity is immutable")
        self._require(item["source_id"])
        self._require(item["target_id"])
        if item["source_id"] == item["target_id"]:
            raise ObjectSystemError("self relationships are not allowed")
        if not item["evidence_refs"]:
            raise ObjectSystemError("relationships require evidence")
        if item["knowledge_state"] not in KNOWLEDGE_STATES:
            raise ObjectSystemError("invalid relationship knowledge state")
        _utc(item["created_at"])
        self._relationships[item["relationship_id"]] = item
        self._record(
            "object.relationship.added",
            item["source_id"],
            item["reason"],
        )
        return deepcopy(item)

    def remove_relationship(
        self, relationship_id: str, *, reason: str
    ) -> dict[str, Any]:
        try:
            item = self._relationships[relationship_id]
        except KeyError as exc:
            raise ObjectSystemError("unknown relationship") from exc
        item["active"] = False
        item["reason"] = reason
        self._record("object.relationship.removed", item["source_id"], reason)
        return deepcopy(item)

    def object(self, object_id: str) -> dict[str, Any] | None:
        item = self._objects.get(object_id)
        return deepcopy(item) if item else None

    def versions(self, object_id: str) -> list[dict[str, Any]]:
        self._require(object_id)
        return deepcopy(self._versions[object_id])

    def neighbors(
        self, object_id: str, relationship_type: str | None = None
    ) -> list[dict[str, Any]]:
        self._require(object_id)
        return [
            deepcopy(item)
            for item in self._relationships.values()
            if item["active"]
            and (item["source_id"] == object_id or item["target_id"] == object_id)
            and (
                relationship_type is None
                or item["relationship_type"] == relationship_type
            )
        ]

    def operational_twin(
        self,
        root_id: str,
        *,
        user_enabled: bool,
        active_mission: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if user_enabled is not True:
            raise ObjectSystemError("Operational Twin view requires user choice")
        root = self._require(root_id)
        relations = self.neighbors(root_id)
        related_ids = {
            relation["target_id"]
            if relation["source_id"] == root_id
            else relation["source_id"]
            for relation in relations
        }
        objects = [deepcopy(root)] + [
            deepcopy(self._require(object_id)) for object_id in sorted(related_ids)
        ]
        return {
            "twin_version": "0.1.0",
            "scope": "operational",
            "simulation": False,
            "authoritative": False,
            "root_id": root_id,
            "objects": objects,
            "relationships": relations,
            "active_mission": deepcopy(dict(active_mission or {})) or None,
            "unknowns": [
                {
                    "object_id": item["object_id"],
                    "fields": deepcopy(item["unknown_fields"]),
                }
                for item in objects
                if item["unknown_fields"]
            ],
        }

    def affected_by_health(self, object_id: str) -> dict[str, Any]:
        item = self._require(object_id)
        return {
            "object_id": object_id,
            "health_state": item["health"]["state"],
            "affected_capabilities": deepcopy(item["capabilities"]),
            "affected_relationships": [
                relation["relationship_id"] for relation in self.neighbors(object_id)
            ],
            "unrelated_objects_remain_available": True,
        }

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def _validate_object(self, item: Mapping[str, Any]) -> None:
        required = {
            "object_id",
            "object_type",
            "display_name",
            "owner_scope",
            "lifecycle_state",
            "knowledge_state",
            "version",
            "capabilities",
            "state",
            "health",
            "limits",
            "policies",
            "evidence_refs",
            "metadata",
            "unknown_fields",
            "creation_source",
            "created_at",
            "updated_at",
            "reason",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise ObjectSystemError(f"object missing fields: {', '.join(missing)}")
        if "." not in item["object_type"]:
            raise ObjectSystemError("object type must be namespaced")
        if item["lifecycle_state"] not in LIFECYCLE:
            raise ObjectSystemError("invalid lifecycle state")
        if item["knowledge_state"] not in KNOWLEDGE_STATES:
            raise ObjectSystemError("invalid knowledge state")
        if item["health"].get("state") not in HEALTH_STATES:
            raise ObjectSystemError("invalid health state")
        if isinstance(item["version"], bool) or not isinstance(item["version"], int):
            raise ObjectSystemError("object version must be an integer")
        if item["version"] < 1:
            raise ObjectSystemError("object version must be positive")
        if not item["evidence_refs"]:
            raise ObjectSystemError("objects require provenance evidence")
        _utc(item["created_at"])
        _utc(item["updated_at"])
        if not isinstance(item["unknown_fields"], list):
            raise ObjectSystemError("unknown_fields must be a list")

    def _require(self, object_id: str) -> dict[str, Any]:
        try:
            return self._objects[object_id]
        except KeyError as exc:
            raise ObjectSystemError(f"unknown object: {object_id}") from exc

    def _record(self, event_type: str, object_id: str, reason: str) -> None:
        self._history.append(
            {"event_type": event_type, "object_id": object_id, "reason": reason}
        )
