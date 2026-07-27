"""FAS-006 envelope validation and idempotent in-memory consumption."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any


class EventError(ValueError):
    """Raised for malformed, duplicate, or out-of-order events."""


_REQUIRED = {
    "event_id",
    "event_type",
    "event_version",
    "occurred_at",
    "published_at",
    "source",
    "subject",
    "correlation_id",
    "causation_id",
    "classification",
    "payload",
    "metadata",
    "trace_id",
}
_CLASSES = {"event", "request", "command", "decision", "evidence", "state"}


def validate_event(event: Mapping[str, Any]) -> dict[str, Any]:
    item = deepcopy(dict(event))
    missing = sorted(_REQUIRED - item.keys())
    if missing:
        raise EventError(f"event missing: {', '.join(missing)}")
    extra = sorted(item.keys() - _REQUIRED)
    if extra:
        raise EventError(f"unknown event fields: {', '.join(extra)}")
    if item["classification"] not in _CLASSES:
        raise EventError("invalid classification")
    for key in ("occurred_at", "published_at"):
        value = item[key]
        if not isinstance(value, str) or not value.endswith("Z"):
            raise EventError(f"{key} must be UTC")
        try:
            datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError as exc:
            raise EventError(f"invalid {key}") from exc
    metadata = item["metadata"]
    for field in ("partition", "sequence", "idempotency_key", "replay", "privacy"):
        if field not in metadata:
            raise EventError(f"metadata missing: {field}")
    if metadata["sequence"] < 0:
        raise EventError("sequence cannot be negative")
    return item


class IdempotentConsumer:
    """Reference at-least-once consumer with per-partition ordering."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._sequences: dict[str, int] = {}

    def accept(self, event: Mapping[str, Any]) -> bool:
        item = validate_event(event)
        event_id = item["event_id"]
        if event_id in self._seen:
            return False
        metadata = item["metadata"]
        partition = metadata["partition"]
        sequence = metadata["sequence"]
        previous = self._sequences.get(partition)
        if previous is not None and sequence <= previous:
            raise EventError("out-of-order partition sequence")
        self._seen.add(event_id)
        self._sequences[partition] = sequence
        return True
