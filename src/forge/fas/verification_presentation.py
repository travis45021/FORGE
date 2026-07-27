"""Plain-language production/twin evidence review before click three."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .twin_comparison import comparison_evidence_digest


class VerificationPresentationError(ValueError):
    """Raised when verification evidence is unsafe or incomplete."""


class VerificationPresenter:
    """Present slicer and twin evidence without converting it into authority."""

    def present(
        self,
        comparison: Mapping[str, Any],
        *,
        limitations: list[str],
    ) -> dict[str, Any]:
        item = deepcopy(dict(comparison))
        evidence_digest = item.get("evidence_digest")
        if (
            not isinstance(evidence_digest, str)
            or comparison_evidence_digest(item) != evidence_digest
        ):
            raise VerificationPresentationError(
                "comparison evidence changed before user review"
            )
        if item.get("can_authorize_production") is not False:
            raise VerificationPresentationError(
                "comparison evidence must remain non-authoritative"
            )
        production = self._mapping(item.get("production"), "production")
        twin = self._mapping(item.get("twin"), "twin")
        acceptance = self._mapping(item.get("acceptance"), "acceptance")
        if production.get("context") != "production" or twin.get("context") != "twin":
            raise VerificationPresentationError("comparison contexts are invalid")
        for result in (production, twin):
            authority = result.get("authority")
            if authority != {"can_upload": False, "can_start_print": False}:
                raise VerificationPresentationError(
                    "slicer evidence cannot grant physical authority"
                )
        warnings = self._plain_list(production.get("warnings"), "warnings")
        twin_warnings = self._plain_list(twin.get("warnings"), "twin warnings")
        limits = self._plain_list(limitations, "limitations")
        differences = self._plain_list(item.get("differences"), "differences")
        matching = (
            acceptance.get("status") == "matching"
            and production.get("status") == "succeeded"
            and twin.get("status") == "succeeded"
            and not differences
        )
        issues = [
            *[f"Production warning: {warning}" for warning in warnings],
            *[f"Twin warning: {warning}" for warning in twin_warnings],
            *[f"Comparison difference: {difference}" for difference in differences],
            *[f"Known limitation: {limitation}" for limitation in limits],
        ]

        return {
            "schema_version": "1.0.0",
            "comparison_id": item.get("comparison_id"),
            "stage": "before_click_three",
            "heading": "Review verification before creating the Print Mission",
            "summary": (
                "Production and twin checks match. Review warnings and limitations "
                "before continuing."
                if matching
                else "Production and twin checks do not match. Resolve the differences "
                "before creating the Print Mission."
            ),
            "verification": {
                "production_status": production.get("status"),
                "twin_status": twin.get("status"),
                "comparison_status": acceptance.get("status"),
                "artifact_digest": production.get("artifact_digest"),
            },
            "issues": [
                {
                    "message": issue,
                    "accessible_label": issue,
                    "non_color_cue": "warning",
                }
                for issue in issues
            ],
            "actions": (
                [
                    {"id": "create_print_mission", "label": "Create Print Mission"},
                    {"id": "change_setup", "label": "Change setup"},
                    {"id": "cancel", "label": "Cancel"},
                ]
                if matching
                else [
                    {"id": "change_setup", "label": "Resolve differences"},
                    {"id": "cancel", "label": "Cancel"},
                ]
            ),
            "can_create_mission": matching,
            "user_review_required": True,
            "twin_is_advisory": True,
            "can_upload": False,
            "can_start_print": False,
            "plain_language": True,
            "accessible_label": (
                "Verification matches and is ready for your review"
                if matching
                else "Verification differs and must be resolved"
            ),
            "non_color_cue": "check" if matching else "warning",
        }

    def confirm_mission_creation(
        self,
        comparison: Mapping[str, Any],
        *,
        limitations: list[str],
        actor: str,
        reviewed_at: str,
        confirmation: bool,
    ) -> dict[str, Any]:
        """Record click three only for matching, user-reviewed evidence."""
        presentation = self.present(comparison, limitations=limitations)
        if not actor.strip() or not reviewed_at.strip() or confirmation is not True:
            raise VerificationPresentationError("named user review is required")
        if presentation["can_create_mission"] is not True:
            raise VerificationPresentationError(
                "different or failed evidence cannot create a Print Mission"
            )
        return {
            "schema_version": "1.0.0",
            "comparison_id": presentation["comparison_id"],
            "artifact_digest": presentation["verification"]["artifact_digest"],
            "stage": "print_mission_creation_requested",
            "reviewed_by": actor.strip(),
            "reviewed_at": reviewed_at.strip(),
            "comparison_evidence_digest": comparison["evidence_digest"],
            "click_number": 3,
            "twin_authority_granted": False,
            "can_upload": False,
            "can_start_print": False,
        }

    @staticmethod
    def _mapping(value: Any, label: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise VerificationPresentationError(f"{label} evidence is missing")
        return value

    @staticmethod
    def _plain_list(value: Any, label: str) -> list[str]:
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            raise VerificationPresentationError(f"{label} must be plain text")
        return deepcopy(value)
