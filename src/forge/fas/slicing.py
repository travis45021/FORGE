"""FORGE-side slicer contracts; this module never controls hardware."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class SlicerContractError(ValueError):
    """Raised when a slicer-boundary object violates FORGE authority rules."""


SUPPORTED_FORMATS = {"step", "stp", "3mf"}
CONTEXTS = {"production", "twin"}
RESULT_STATES = {"succeeded", "failed", "cancelled", "timed_out"}


class SlicerContractBoundary:
    """Validate contract objects while denying upload and print authority."""

    def request(self, value: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(value))
        required = {
            "contract_version",
            "request_id",
            "input",
            "context",
            "profile_digest",
            "authority",
        }
        self._require(item, required, "request")
        self._version(item)
        source = item["input"]
        if not isinstance(source, Mapping):
            raise SlicerContractError("request input must be an object")
        self._require(source, {"format", "digest", "path"}, "request input")
        if source["format"] not in SUPPORTED_FORMATS:
            raise SlicerContractError("only STEP/STP and 3MF are supported")
        if item["context"] not in CONTEXTS:
            raise SlicerContractError("context must be production or twin")
        self._digest(source["digest"], "input digest")
        self._digest(item["profile_digest"], "profile digest")
        authority = item["authority"]
        if (
            not isinstance(authority, Mapping)
            or authority.get("user_confirmation_stage") != "created_mission"
        ):
            raise SlicerContractError("request requires a created Mission")
        return item

    def result(self, value: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(value))
        self._require(
            item,
            {
                "contract_version",
                "request_id",
                "status",
                "context",
                "engine",
                "warnings",
                "authority",
            },
            "result",
        )
        self._version(item)
        if item["status"] not in RESULT_STATES or item["context"] not in CONTEXTS:
            raise SlicerContractError("invalid result state or context")
        authority = item["authority"]
        if not isinstance(authority, Mapping) or authority != {
            "can_upload": False,
            "can_start_print": False,
        }:
            raise SlicerContractError("slicer results cannot grant physical authority")
        engine = item["engine"]
        if not isinstance(engine, Mapping):
            raise SlicerContractError("engine provenance is required")
        self._require(engine, {"name", "version", "source_digest"}, "engine")
        self._digest(engine["source_digest"], "engine source digest")
        return item

    @staticmethod
    def _require(value: Mapping[str, Any], fields: set[str], label: str) -> None:
        missing = sorted(fields - value.keys())
        if missing:
            raise SlicerContractError(f"{label} missing: {', '.join(missing)}")

    @staticmethod
    def _digest(value: Any, label: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise SlicerContractError(f"{label} must be lowercase SHA-256")

    @staticmethod
    def _version(value: Mapping[str, Any]) -> None:
        if value.get("contract_version") != "1.0":
            raise SlicerContractError("unsupported slicer contract version")
