"""Plain-language presentation of a governed upload-dispatch outcome."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class DispatchPresentationError(ValueError):
    """Raised when a dispatch outcome cannot be presented safely."""


class DispatchOutcomePresenter:
    """Explain Runtime dispatch without claiming a printer-side outcome."""

    def present(self, result: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(result))
        if (
            item.get("upload_dispatched") is not True
            or item.get("print_started") is not False
            or item.get("physical_outcome_confirmed") is not False
        ):
            raise DispatchPresentationError(
                "only a non-physical upload dispatch can use this presentation"
            )
        evidence = item.get("upload_evidence")
        runtime = item.get("runtime_result")
        if not isinstance(evidence, Mapping) or not isinstance(runtime, Mapping):
            raise DispatchPresentationError(
                "dispatch evidence and Runtime result are required"
            )
        if (
            evidence.get("fourth_click_satisfied") is not True
            or evidence.get("physical_dispatch_allowed") is not False
            or runtime.get("status") != "dispatched"
            or runtime.get("physical_outcome_confirmed") is not False
        ):
            raise DispatchPresentationError("dispatch evidence is inconsistent")
        for field in ("job_id", "provider_id"):
            value = evidence.get(field)
            if not isinstance(value, str) or not value.strip():
                raise DispatchPresentationError(
                    f"dispatch {field.replace('_', ' ')} is invalid"
                )
            if runtime.get(field) != value:
                raise DispatchPresentationError(
                    f"Runtime {field.replace('_', ' ')} does not match upload evidence"
                )
        for field in (
            "artifact_digest",
            "final_confirmation_evidence_digest",
        ):
            value = evidence.get(field)
            if not self._digest(value):
                raise DispatchPresentationError(
                    f"dispatch {field.replace('_', ' ')} is invalid"
                )
        if runtime.get("artifact_digest") != evidence["artifact_digest"]:
            raise DispatchPresentationError(
                "Runtime artifact does not match upload evidence"
            )
        if not self._digest(runtime.get("provider_dispatch_evidence_digest")):
            raise DispatchPresentationError(
                "provider dispatch evidence digest is invalid"
            )
        if (
            "confirmation_token" in evidence
            or "final_confirmation_evidence" in evidence
        ):
            raise DispatchPresentationError(
                "secret confirmation material cannot enter presentation"
            )
        return {
            "schema_version": "1.0.0",
            "stage": "upload_command_dispatched",
            "heading": "Print upload sent",
            "summary": (
                "FORGE sent the verified upload command to the printer provider. "
                "The printer has not yet confirmed receipt or started printing."
            ),
            "job_id": evidence.get("job_id"),
            "provider_id": evidence.get("provider_id"),
            "artifact_digest": evidence.get("artifact_digest"),
            "final_confirmation_evidence_digest": evidence.get(
                "final_confirmation_evidence_digest"
            ),
            "provider_dispatch_evidence_digest": runtime.get(
                "provider_dispatch_evidence_digest"
            ),
            "actions": [
                {"id": "view_job_status", "label": "View job status"},
                {"id": "view_evidence", "label": "View evidence"},
            ],
            "upload_command_dispatched": True,
            "printer_receipt_confirmed": False,
            "print_started": False,
            "physical_outcome_confirmed": False,
            "start_control_enabled": False,
            "can_upload": False,
            "can_start_print": False,
            "plain_language": True,
            "accessible_label": (
                "Upload command sent. Printer receipt and print start are not confirmed."
            ),
            "non_color_cue": "waiting",
        }

    @staticmethod
    def _digest(value: Any) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )
