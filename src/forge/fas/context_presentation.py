"""Plain-language print-context review before the second user click."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class ContextPresentationError(ValueError):
    """Raised when inferred print context is incomplete or silently trusted."""


class PrintContextPresenter:
    """Present inference as reviewable evidence, never as user authority."""

    def present(self, context: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(context))
        required = {
            "context_id",
            "source_digest",
            "printer",
            "material",
            "process",
            "safety",
            "assumptions",
            "missing_information",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise ContextPresentationError(
                f"print context missing: {', '.join(missing)}"
            )
        self._digest(item["source_digest"], "source digest")
        printer = self._mapping(item["printer"], "printer")
        material = self._mapping(item["material"], "material")
        process = self._mapping(item["process"], "process")
        safety = self._mapping(item["safety"], "safety")
        if not printer.get("provider_id") or not printer.get("capabilities"):
            raise ContextPresentationError(
                "printer provider and capabilities are required"
            )
        if not material.get("name") or not material.get("source"):
            raise ContextPresentationError(
                "material name and inference source are required"
            )
        if not process.get("name") or not process.get("source"):
            raise ContextPresentationError(
                "process name and inference source are required"
            )
        if safety.get("status") not in {"passed", "needs_review", "unavailable"}:
            raise ContextPresentationError("safety status is invalid")
        assumptions = self._plain_list(item["assumptions"], "assumptions")
        missing_information = self._plain_list(
            item["missing_information"], "missing information"
        )
        can_confirm = not missing_information and safety["status"] == "passed"

        return {
            "schema_version": "1.0.0",
            "context_id": item["context_id"],
            "stage": "before_click_two",
            "heading": "Review your print setup",
            "summary": (
                "FORGE inferred this setup from your file and local configuration. "
                "Check every item before continuing."
            ),
            "sections": {
                "printer": {
                    "label": printer.get("display_name", printer["provider_id"]),
                    "provider_id": printer["provider_id"],
                    "capabilities": deepcopy(printer["capabilities"]),
                    "source": printer.get("source", "local capability provider"),
                },
                "material": {
                    "label": material["name"],
                    "source": material["source"],
                },
                "process": {
                    "label": process["name"],
                    "source": process["source"],
                },
                "safety": {
                    "status": safety["status"],
                    "summary": safety.get(
                        "summary", "No safety explanation was provided."
                    ),
                    "non_color_cue": (
                        "check" if safety["status"] == "passed" else "warning"
                    ),
                },
            },
            "assumptions": assumptions,
            "missing_information": missing_information,
            "actions": (
                [
                    {"id": "confirm_context", "label": "Use this setup"},
                    {"id": "edit_context", "label": "Change setup"},
                    {"id": "cancel_import", "label": "Cancel"},
                ]
                if can_confirm
                else [
                    {"id": "edit_context", "label": "Resolve setup"},
                    {"id": "cancel_import", "label": "Cancel"},
                ]
            ),
            "can_confirm": can_confirm,
            "user_confirmation_required": True,
            "can_slice": False,
            "can_upload": False,
            "can_start_print": False,
            "plain_language": True,
            "accessible_label": (
                "Print setup ready for your confirmation"
                if can_confirm
                else "Print setup needs changes before confirmation"
            ),
        }

    def confirm(
        self,
        context: Mapping[str, Any],
        *,
        actor: str,
        confirmation: bool,
    ) -> dict[str, Any]:
        """Record click two only when the displayed context is complete."""
        presentation = self.present(context)
        if not actor.strip() or confirmation is not True:
            raise ContextPresentationError("named user confirmation is required")
        if presentation["can_confirm"] is not True:
            raise ContextPresentationError("incomplete context cannot be confirmed")
        return {
            "schema_version": "1.0.0",
            "context_id": presentation["context_id"],
            "stage": "context_confirmed",
            "confirmed_by": actor.strip(),
            "click_number": 2,
            "can_authorize_production": False,
        }

    @staticmethod
    def _mapping(value: Any, label: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ContextPresentationError(f"{label} context must be an object")
        return value

    @staticmethod
    def _plain_list(value: Any, label: str) -> list[str]:
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            raise ContextPresentationError(f"{label} must be plain text")
        return deepcopy(value)

    @staticmethod
    def _digest(value: Any, label: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ContextPresentationError(f"{label} must be lowercase SHA-256")
