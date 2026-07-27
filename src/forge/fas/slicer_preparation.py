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
        derived_profile: Mapping[str, Any],
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
        profile = dict(derived_profile)
        if (
            profile.get("lifecycle") != "ephemeral"
            or profile.get("persist_after_worker") is not False
            or profile.get("delete_after_result") is not True
            or profile.get("hardware_neutral") is not True
            or profile.get("contains_transport_endpoint") is not False
            or profile.get("contains_credentials") is not False
            or profile.get("cloud_access") is not False
            or profile.get("can_control_printer") is not False
            or profile.get("can_upload") is not False
            or profile.get("can_start_print") is not False
        ):
            raise SlicerPreparationError(
                "derived worker profile violates the ephemeral authority boundary"
            )
        profile_digest = profile.get("profile_digest")
        if (
            not isinstance(profile_digest, str)
            or len(profile_digest) != 64
            or any(character not in "0123456789abcdef" for character in profile_digest)
        ):
            raise SlicerPreparationError(
                "derived profile digest must be lowercase SHA-256"
            )
        if not isinstance(profile.get("content"), Mapping):
            raise SlicerPreparationError("derived profile content is required")

        request = {
            "contract_version": "1.0",
            "request_id": request_id,
            "input": {
                "format": assessment["format"],
                "digest": assessment["source_digest"],
                "path": source_path,
            },
            "context": context,
            "profile_digest": profile_digest,
            "authority": {
                "mission_id": mission_id,
                "user_confirmation_stage": "created_mission",
            },
            "settings": dict(profile["content"]),
            "profile_ephemeral": True,
        }
        try:
            return self._boundary.request(request)
        except SlicerContractError as exc:
            raise SlicerPreparationError(str(exc)) from exc
