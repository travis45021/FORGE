"""Validated Manufacturing Intent without physical authority."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


class ManufacturingIntentError(ValueError):
    """Raised when manufacturing intent is incomplete or unsupported."""


class ManufacturingIntentService:
    """Validate user-confirmed intent before producing slicer requests."""

    def validate(self, value: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(value))
        required = {
            "intent_id",
            "source_digest",
            "printer_capabilities",
            "material",
            "process",
            "user_decisions",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise ManufacturingIntentError(f"intent missing: {', '.join(missing)}")
        self._digest(item["source_digest"], "source digest")

        capabilities = item["printer_capabilities"]
        if (
            not isinstance(capabilities, Sequence)
            or isinstance(capabilities, (str, bytes))
            or not capabilities
            or any(not isinstance(value, str) or not value for value in capabilities)
        ):
            raise ManufacturingIntentError("printer capabilities must be declared")

        material = item["material"]
        process = item["process"]
        if not isinstance(material, Mapping) or not material.get("name"):
            raise ManufacturingIntentError("material name is required")
        if not isinstance(process, Mapping):
            raise ManufacturingIntentError("process profile is required")
        self._digest(process.get("profile_digest"), "profile digest")

        decisions = item["user_decisions"]
        if not isinstance(decisions, Mapping) or decisions != {
            "context_confirmed": True,
            "mission_reviewed": True,
        }:
            raise ManufacturingIntentError(
                "user must confirm context and review the Mission"
            )

        item["can_authorize_production"] = False
        return item

    @staticmethod
    def _digest(value: Any, label: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ManufacturingIntentError(f"{label} must be lowercase SHA-256")
