"""Plain-language production/twin evidence review before click three."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
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
        expected_fields = {
            "comparison_id",
            "input_digest",
            "profile_digest",
            "production",
            "twin",
            "differences",
            "acceptance",
            "pair_preflight_verified",
            "can_authorize_production",
            "evidence_digest",
        }
        if set(item) != expected_fields:
            raise VerificationPresentationError(
                "comparison evidence fields are invalid"
            )
        if (
            not isinstance(item["comparison_id"], str)
            or not item["comparison_id"].strip()
            or not self._digest(item["input_digest"])
            or not self._digest(item["profile_digest"])
            or item["pair_preflight_verified"] is not True
        ):
            raise VerificationPresentationError(
                "coordinated pair-preflight lineage is required"
            )
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
        expected_acceptance = {
            "status",
            "reviewed_by_user",
            "preflight_evidence_required",
            "pair_preflight_required",
        }
        if (
            set(acceptance) != expected_acceptance
            or acceptance.get("reviewed_by_user") is not False
            or acceptance.get("preflight_evidence_required") is not True
            or acceptance.get("pair_preflight_required") is not True
        ):
            raise VerificationPresentationError(
                "comparison acceptance is not pair-preflight evidence"
            )
        if production.get("context") != "production" or twin.get("context") != "twin":
            raise VerificationPresentationError("comparison contexts are invalid")
        for result in (production, twin):
            authority = result.get("authority")
            if authority != {"can_upload": False, "can_start_print": False}:
                raise VerificationPresentationError(
                    "slicer evidence cannot grant physical authority"
                )
            if (
                result.get("status") != "succeeded"
                or result.get("preflight_verified") is not True
                or not isinstance(result.get("request_id"), str)
                or not result["request_id"]
                or not self._digest(result.get("artifact_digest"))
            ):
                raise VerificationPresentationError(
                    "complete preflighted slicer evidence is required"
                )
            self._engine(result.get("engine"))
        warnings = self._plain_list(production.get("warnings"), "warnings")
        twin_warnings = self._plain_list(twin.get("warnings"), "twin warnings")
        limits = self._plain_list(limitations, "limitations")
        differences = self._plain_list(item.get("differences"), "differences")
        calculated_differences = []
        for field in ("artifact_digest", "engine", "warnings"):
            if production.get(field) != twin.get(field):
                calculated_differences.append(field)
        if differences != calculated_differences:
            raise VerificationPresentationError(
                "comparison differences are inconsistent"
            )
        expected_status = "matching" if not differences else "different"
        if acceptance.get("status") != expected_status:
            raise VerificationPresentationError("comparison acceptance is inconsistent")
        matching = acceptance.get("status") == "matching" and not differences
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
        if not isinstance(actor, str) or not actor.strip() or confirmation is not True:
            raise VerificationPresentationError("named user review is required")
        self._utc(reviewed_at)
        if presentation["can_create_mission"] is not True:
            raise VerificationPresentationError(
                "different or failed evidence cannot create a Print Mission"
            )
        return {
            "schema_version": "1.0.0",
            "comparison_id": presentation["comparison_id"],
            "input_digest": comparison["input_digest"],
            "profile_digest": comparison["profile_digest"],
            "artifact_digest": presentation["verification"]["artifact_digest"],
            "engine_source_digest": comparison["production"]["engine"]["source_digest"],
            "engine_build_digest": comparison["production"]["engine"]["build_digest"],
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

    @staticmethod
    def _digest(value: Any) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )

    @classmethod
    def _engine(cls, value: Any) -> None:
        if (
            not isinstance(value, Mapping)
            or set(value)
            != {
                "name",
                "version",
                "source_digest",
                "build_digest",
            }
            or not isinstance(value["name"], str)
            or not value["name"]
            or not isinstance(value["version"], str)
            or not value["version"]
            or not cls._digest(value["source_digest"])
            or not cls._digest(value["build_digest"])
        ):
            raise VerificationPresentationError("slicer engine provenance is invalid")

    @staticmethod
    def _utc(value: Any) -> None:
        if not isinstance(value, str) or not value.endswith("Z"):
            raise VerificationPresentationError(
                "verification review timestamp must be UTC"
            )
        try:
            datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError as exc:
            raise VerificationPresentationError(
                "verification review timestamp is invalid"
            ) from exc
