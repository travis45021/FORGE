"""Prepare governed slicer requests from validated FORGE evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .manufacturing_intent import ManufacturingIntentError, ManufacturingIntentService
from .slicing import SlicerContractBoundary, SlicerContractError


class SlicerPreparationError(ValueError):
    """Raised when quarantine and intent evidence cannot form a safe request."""


class SlicerMissionPreparation:
    """Join accepted import evidence and user-confirmed intent."""

    def __init__(self) -> None:
        self._intents = ManufacturingIntentService()
        self._boundary = SlicerContractBoundary()

    def prepare(
        self,
        *,
        request_id: str,
        mission_id: str,
        source_path: str,
        context: str,
        assessment: Mapping[str, Any],
        intent: Mapping[str, Any],
        settings: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if assessment.get("decision") != "accepted":
            raise SlicerPreparationError("import assessment must be accepted")
        quarantine = assessment.get("quarantine")
        if (
            not isinstance(quarantine, Mapping)
            or quarantine.get("isolated") is not True
        ):
            raise SlicerPreparationError("import must remain isolated")
        if assessment.get("can_authorize_production") is not False:
            raise SlicerPreparationError("import evidence must be non-authoritative")
        try:
            validated_intent = self._intents.validate(intent)
        except ManufacturingIntentError as exc:
            raise SlicerPreparationError(str(exc)) from exc
        if validated_intent["source_digest"] != assessment.get("source_digest"):
            raise SlicerPreparationError("assessment and intent source digests differ")

        request = {
            "request_id": request_id,
            "input": {
                "format": assessment["format"],
                "digest": assessment["source_digest"],
                "path": source_path,
            },
            "context": context,
            "profile_digest": validated_intent["process"]["profile_digest"],
            "authority": {
                "mission_id": mission_id,
                "user_confirmation_stage": "created_mission",
            },
            "settings": dict(settings or {}),
        }
        try:
            return self._boundary.request(request)
        except SlicerContractError as exc:
            raise SlicerPreparationError(str(exc)) from exc
