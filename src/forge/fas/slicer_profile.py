"""Ephemeral hardware-neutral slicer profiles derived from FORGE evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from typing import Any

from .manufacturing_intent import ManufacturingIntentError, ManufacturingIntentService


class SlicerProfileError(ValueError):
    """Raised when trusted evidence cannot form an ephemeral worker profile."""


FORBIDDEN_PROFILE_KEYS = {
    "credential",
    "credentials",
    "password",
    "token",
    "secret",
    "endpoint",
    "hostname",
    "ip_address",
    "cloud",
    "printer_control",
}


class SlicerProfileAdapter:
    """Derive data-only worker settings without transport or physical authority."""

    def derive(
        self,
        *,
        machine: Mapping[str, Any],
        configuration: Mapping[str, Any],
        intent: Mapping[str, Any],
    ) -> dict[str, Any]:
        machine_item = deepcopy(dict(machine))
        required_machine = {
            "object_id",
            "version",
            "lifecycle_state",
            "knowledge_state",
            "health",
            "capabilities",
            "limits",
            "unknown_fields",
            "evidence_refs",
        }
        missing = sorted(required_machine - machine_item.keys())
        if missing:
            raise SlicerProfileError(f"machine object missing: {', '.join(missing)}")
        if machine_item["lifecycle_state"] not in {"validated", "active"}:
            raise SlicerProfileError("machine object must be validated or active")
        if machine_item["knowledge_state"] not in {"locally_measured", "validated"}:
            raise SlicerProfileError("machine knowledge must be measured or validated")
        if machine_item["health"].get("state") != "healthy":
            raise SlicerProfileError("machine health must be current and healthy")
        if machine_item["unknown_fields"]:
            raise SlicerProfileError("machine unknowns require user resolution")
        if not machine_item["capabilities"] or not machine_item["evidence_refs"]:
            raise SlicerProfileError("machine capabilities and evidence are required")

        configuration_item = deepcopy(dict(configuration))
        if set(configuration_item) != {"profile_ids", "values", "hard_limits"}:
            raise SlicerProfileError("resolved configuration shape is invalid")
        if not configuration_item["profile_ids"]:
            raise SlicerProfileError("resolved configuration profiles are required")
        self._reject_forbidden(configuration_item)

        try:
            intent_item = ManufacturingIntentService().validate(intent)
        except ManufacturingIntentError as exc:
            raise SlicerProfileError(str(exc)) from exc
        if not set(intent_item["printer_capabilities"]) <= set(
            machine_item["capabilities"]
        ):
            raise SlicerProfileError(
                "machine does not satisfy Manufacturing Intent capabilities"
            )
        self._reject_forbidden(intent_item["material"])
        self._reject_forbidden(intent_item["process"])

        content = {
            "machine": {
                "object_id": machine_item["object_id"],
                "version": machine_item["version"],
                "capabilities": sorted(machine_item["capabilities"]),
                "limits": deepcopy(machine_item["limits"]),
                "evidence_refs": sorted(machine_item["evidence_refs"]),
            },
            "configuration": configuration_item,
            "material": deepcopy(intent_item["material"]),
            "process": deepcopy(intent_item["process"]),
        }
        canonical = json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return {
            "schema_version": "1.0.0",
            "profile_digest": sha256(canonical).hexdigest(),
            "content": content,
            "lifecycle": "ephemeral",
            "persist_after_worker": False,
            "delete_after_result": True,
            "hardware_neutral": True,
            "contains_transport_endpoint": False,
            "contains_credentials": False,
            "cloud_access": False,
            "can_control_printer": False,
            "can_upload": False,
            "can_start_print": False,
        }

    @classmethod
    def _reject_forbidden(cls, value: Any) -> None:
        if isinstance(value, Mapping):
            forbidden = {
                str(key).lower()
                for key in value
                if str(key).lower() in FORBIDDEN_PROFILE_KEYS
            }
            if forbidden:
                raise SlicerProfileError(
                    "worker profile contains forbidden fields: "
                    + ", ".join(sorted(forbidden))
                )
            for child in value.values():
                cls._reject_forbidden(child)
        elif isinstance(value, list):
            for child in value:
                cls._reject_forbidden(child)
