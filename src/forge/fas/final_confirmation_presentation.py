"""Accessible live-check review for the mandatory fourth click."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any

from .live_printer_checks import (
    REQUIRED_CHECKS,
    live_check_evidence_digest,
)


class FinalConfirmationPresentationError(ValueError):
    """Raised when the final confirmation cannot be safely presented."""


CHECK_LABELS = {
    "connected": "Printer is connected",
    "idle": "Printer is idle",
    "capabilities_match": "Printer capabilities match this job",
    "material_available": "Required material is available",
    "safety_state_clear": "Live safety state is clear",
    "artifact_current": "The verified print artifact is current",
}


class FinalConfirmationPresenter:
    """Present live evidence immediately before controlled upload."""

    def present(
        self,
        live_checks: Mapping[str, Any],
        *,
        printer_name: str,
        job_name: str,
        presented_at: str,
    ) -> dict[str, Any]:
        item = deepcopy(dict(live_checks))
        if (
            not isinstance(printer_name, str)
            or not printer_name.strip()
            or not isinstance(job_name, str)
            or not job_name.strip()
        ):
            raise FinalConfirmationPresentationError(
                "printer and job names are required"
            )
        expected_fields = {
            "provider_id",
            "artifact_digest",
            "checks",
            "checked_at",
            "expires_at",
            "passed",
            "failed_checks",
            "final_confirmation_required",
            "can_upload",
            "can_start_print",
            "evidence_digest",
        }
        if set(item) != expected_fields:
            raise FinalConfirmationPresentationError("live evidence fields are invalid")
        if (
            not isinstance(item["provider_id"], str)
            or not item["provider_id"]
            or not self._digest(item["artifact_digest"])
        ):
            raise FinalConfirmationPresentationError(
                "live evidence identity is invalid"
            )
        if item["evidence_digest"] != live_check_evidence_digest(item):
            raise FinalConfirmationPresentationError("live evidence digest is invalid")
        checked_at = self._utc(item["checked_at"])
        expires_at = self._utc(item["expires_at"])
        now = self._utc(presented_at)
        if now < checked_at:
            raise FinalConfirmationPresentationError(
                "live evidence cannot be presented before it was checked"
            )
        if now >= expires_at:
            raise FinalConfirmationPresentationError(
                "live evidence expired before final confirmation"
            )
        if item.get("final_confirmation_required") is not True:
            raise FinalConfirmationPresentationError(
                "live evidence must require final confirmation"
            )
        if (
            item.get("can_upload") is not False
            or item.get("can_start_print") is not False
        ):
            raise FinalConfirmationPresentationError(
                "live evidence must remain non-authoritative"
            )
        checks = item.get("checks")
        if not isinstance(checks, Mapping) or set(checks) != REQUIRED_CHECKS:
            raise FinalConfirmationPresentationError(
                "complete live printer checks are required"
            )
        if any(not isinstance(value, bool) for value in checks.values()):
            raise FinalConfirmationPresentationError(
                "live printer check results must be boolean"
            )
        failed = sorted(name for name in REQUIRED_CHECKS if checks[name] is not True)
        if sorted(item.get("failed_checks", [])) != failed:
            raise FinalConfirmationPresentationError(
                "failed-check evidence is inconsistent"
            )
        if item.get("passed") is not (not failed):
            raise FinalConfirmationPresentationError(
                "live pass evidence is inconsistent"
            )
        passed = not failed

        return {
            "schema_version": "1.0.0",
            "stage": "before_click_four",
            "heading": "Final check before printing",
            "summary": (
                f"{job_name.strip()} is ready for your final approval on "
                f"{printer_name.strip()}."
                if passed
                else "One or more live printer checks failed. Printing is blocked."
            ),
            "printer_name": printer_name.strip(),
            "job_name": job_name.strip(),
            "checks": [
                {
                    "id": name,
                    "label": CHECK_LABELS[name],
                    "passed": checks[name],
                    "accessible_label": (
                        f"Passed: {CHECK_LABELS[name]}"
                        if checks[name]
                        else f"Failed: {CHECK_LABELS[name]}"
                    ),
                    "non_color_cue": "check" if checks[name] else "blocked",
                }
                for name in sorted(REQUIRED_CHECKS)
            ],
            "actions": (
                [
                    {"id": "yes_print", "label": "Yes, Print"},
                    {"id": "cancel", "label": "Cancel"},
                ]
                if passed
                else [
                    {"id": "run_checks_again", "label": "Run checks again"},
                    {"id": "cancel", "label": "Cancel"},
                ]
            ),
            "can_confirm": passed,
            "confirmation_label": "Yes, Print",
            "confirmation_is_fourth_click": True,
            "bypass_enabled": False,
            "can_upload": False,
            "can_start_print": False,
            "plain_language": True,
            "accessible_label": (
                "All live checks passed. Yes, Print is available."
                if passed
                else f"Printing blocked. {len(failed)} live checks failed."
            ),
            "non_color_cue": "check" if passed else "blocked",
        }

    def confirm(
        self,
        live_checks: Mapping[str, Any],
        *,
        printer_name: str,
        job_name: str,
        actor: str,
        action: str,
        presented_at: str,
    ) -> dict[str, Any]:
        """Record the explicit fourth click without dispatching hardware."""
        presentation = self.present(
            live_checks,
            printer_name=printer_name,
            job_name=job_name,
            presented_at=presented_at,
        )
        if (
            presentation["can_confirm"] is not True
            or action != "yes_print"
            or not isinstance(actor, str)
            or not actor.strip()
        ):
            raise FinalConfirmationPresentationError(
                "Yes, Print requires passed live checks and a named user"
            )
        return {
            "schema_version": "1.0.0",
            "provider_id": live_checks.get("provider_id"),
            "artifact_digest": live_checks.get("artifact_digest"),
            "live_checks_evidence_digest": live_checks.get("evidence_digest"),
            "live_checks_expires_at": live_checks.get("expires_at"),
            "stage": "final_confirmation_recorded",
            "confirmed_by": actor.strip(),
            "confirmed_at": presented_at,
            "action": "Yes, Print",
            "click_number": 4,
            "requires_controlled_upload": True,
            "physical_dispatch_allowed": False,
        }

    @staticmethod
    def _utc(value: Any) -> datetime:
        if not isinstance(value, str) or not value.endswith("Z"):
            raise FinalConfirmationPresentationError(
                "confirmation presentation timestamps must be UTC"
            )
        try:
            return datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError as exc:
            raise FinalConfirmationPresentationError(
                "confirmation presentation timestamp is invalid"
            ) from exc

    @staticmethod
    def _digest(value: Any) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )
