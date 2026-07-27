"""Plain-language, presentation-neutral STEP/3MF import status."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class ImportPresentationError(ValueError):
    """Raised when import evidence cannot be presented safely."""


class ImportStatusPresenter:
    """Translate quarantine evidence without hiding or overriding ambiguity."""

    def present(self, assessment: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(assessment))
        decision = item.get("decision")
        if decision not in {"accepted", "needs_user_resolution"}:
            raise ImportPresentationError("unknown import assessment decision")
        if item.get("format") not in {"step", "stp", "3mf"}:
            raise ImportPresentationError("unknown import format")
        if item.get("can_authorize_production") is not False:
            raise ImportPresentationError("import evidence must be non-authoritative")
        quarantine = item.get("quarantine")
        if (
            not isinstance(quarantine, Mapping)
            or quarantine.get("isolated") is not True
        ):
            raise ImportPresentationError("input must remain isolated")
        ambiguities = item.get("ambiguities")
        if not isinstance(ambiguities, list) or any(
            not isinstance(value, str) or not value.strip() for value in ambiguities
        ):
            raise ImportPresentationError("import ambiguities must be plain text")

        accepted = decision == "accepted"
        if accepted and ambiguities:
            raise ImportPresentationError("accepted input cannot retain ambiguities")
        if not accepted and not ambiguities:
            raise ImportPresentationError("resolution state requires an explanation")

        return {
            "schema_version": "1.0.0",
            "kind": "status" if accepted else "warning",
            "status": "ready_for_context_review" if accepted else "needs_your_review",
            "heading": (
                "File checks passed" if accepted else "This file needs your review"
            ),
            "summary": (
                "FORGE safely read the file structure. Review the printer, "
                "material, and process next."
                if accepted
                else "FORGE found information that is missing or unclear. "
                "Nothing will be sliced or printed until you resolve it."
            ),
            "format_label": "STEP" if item["format"] in {"step", "stp"} else "3MF",
            "issues": [
                {
                    "message": ambiguity,
                    "accessible_label": f"File issue: {ambiguity}",
                    "non_color_cue": "warning",
                }
                for ambiguity in ambiguities
            ],
            "actions": (
                [{"id": "review_context", "label": "Review print setup"}]
                if accepted
                else [
                    {"id": "open_builder", "label": "Review in Builder"},
                    {"id": "replace_file", "label": "Choose another file"},
                    {"id": "cancel_import", "label": "Cancel import"},
                ]
            ),
            "resolution_required": not accepted,
            "can_continue": accepted,
            "can_slice": False,
            "can_upload": False,
            "can_start_print": False,
            "plain_language": True,
            "accessible_label": (
                "File checks passed"
                if accepted
                else f"File needs review. {len(ambiguities)} issues found."
            ),
            "non_color_cue": "check" if accepted else "warning",
        }

    def record_resolution(
        self,
        assessment: Mapping[str, Any],
        *,
        action: str,
        actor: str,
    ) -> dict[str, Any]:
        """Record a user choice without treating it as validation."""
        presentation = self.present(assessment)
        if not presentation["resolution_required"]:
            raise ImportPresentationError("accepted input does not need resolution")
        allowed = {"open_builder", "replace_file", "cancel_import"}
        if action not in allowed or not actor.strip():
            raise ImportPresentationError(
                "a named user and valid resolution are required"
            )
        return {
            "schema_version": "1.0.0",
            "assessment_id": assessment.get("assessment_id"),
            "actor": actor.strip(),
            "action": action,
            "status": {
                "open_builder": "awaiting_builder_review",
                "replace_file": "awaiting_replacement",
                "cancel_import": "cancelled",
            }[action],
            "ambiguity_overridden": False,
            "can_authorize_production": False,
        }
