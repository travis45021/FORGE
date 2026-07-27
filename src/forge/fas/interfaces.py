"""Local-first interface gateway for canonical FAS-024."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any


class InterfaceError(ValueError):
    """Raised when an interface request violates FAS-024."""


INTERFACE_MODES = {"simple", "builder", "advanced", "accessible", "developer"}
CONTENT_KINDS = {"status", "alert", "suggestion", "approval", "decision", "error"}
LOCAL_API_VERSION = "v1"
PRINT_WORKFLOW_SCREENS = {
    "add_file",
    "confirm_context",
    "create_print_mission",
    "yes_print",
    "print_dispatch_status",
}


class InterfaceGateway:
    """A presentation-neutral gateway into the Executive request path."""

    def __init__(
        self,
        executive_request: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        *,
        supported_versions: tuple[str, ...] = (LOCAL_API_VERSION,),
    ) -> None:
        self._executive_request = executive_request
        self._versions = supported_versions
        self._subscriptions: dict[str, set[str]] = {}

    def negotiate(self, client_versions: list[str]) -> dict[str, Any]:
        matches = [version for version in self._versions if version in client_versions]
        if not matches:
            return self.error(
                reason="unsupported_api_version",
                summary="This client does not support a compatible local API version.",
                affected_object="interface",
                next_step=f"Use one of: {', '.join(self._versions)}.",
            )
        return {"ok": True, "api_version": matches[0], "transport": "local"}

    def submit(
        self,
        request: Mapping[str, Any],
        *,
        authenticated_identity: str | None,
        api_version: str,
        transport: str = "local",
    ) -> dict[str, Any]:
        if transport != "local":
            raise InterfaceError("remote and cloud transports are outside FORGE v1")
        if api_version not in self._versions:
            raise InterfaceError("unsupported API version")
        if not authenticated_identity:
            raise InterfaceError("authenticated local identity is required")
        item = deepcopy(dict(request))
        required = {"request_id", "action", "target", "parameters"}
        missing = sorted(required - item.keys())
        if missing:
            raise InterfaceError(f"request missing fields: {', '.join(missing)}")
        if item.get("raw_hardware_command") is not None:
            raise InterfaceError("the local API is not a raw-hardware API")
        item["requester"] = authenticated_identity
        item["source"] = "interface_gateway"
        item["api_version"] = api_version
        result = dict(self._executive_request(deepcopy(item)))
        return {"ok": True, "request": item, "executive_result": result}

    def action_summary(
        self,
        action: Mapping[str, Any],
        *,
        mode: str = "simple",
    ) -> dict[str, Any]:
        self._mode(mode)
        required = {
            "summary",
            "target",
            "reason",
            "safety_conditions",
            "reversible",
            "failure_response",
            "approval_scope",
            "data_behavior",
        }
        missing = sorted(required - action.keys())
        if missing:
            raise InterfaceError(f"action explanation missing: {', '.join(missing)}")
        result = {
            "what_will_happen": action["summary"],
            "affected_object": action["target"],
            "why": action["reason"],
            "safety_conditions": deepcopy(action["safety_conditions"]),
            "reversible": action["reversible"],
            "failure_response": action["failure_response"],
            "approval_scope": action["approval_scope"],
            "data_behavior": action["data_behavior"],
            "plain_language": True,
        }
        if mode in {"advanced", "developer"}:
            result["evidence"] = deepcopy(action.get("evidence", []))
            result["policy_refs"] = deepcopy(action.get("policy_refs", []))
        return result

    def approval_summary(self, approval: Mapping[str, Any]) -> dict[str, Any]:
        required = {
            "requester",
            "action",
            "scope",
            "expires_at",
            "targets",
            "risks",
            "verification_state",
            "grant_type",
            "revocation_method",
        }
        missing = sorted(required - approval.keys())
        if missing:
            raise InterfaceError(f"approval explanation missing: {', '.join(missing)}")
        if approval["grant_type"] not in {"once", "mission", "standing_policy"}:
            raise InterfaceError("approval grant type must be explicit")
        result = deepcopy(dict(approval))
        result["standing_authority_warning"] = (
            approval["grant_type"] == "standing_policy"
        )
        return result

    def content(
        self,
        *,
        kind: str,
        text: str,
        accessible_label: str,
        cue: str,
        mode: str = "simple",
        suggestions_enabled: bool = True,
    ) -> dict[str, Any] | None:
        self._mode(mode)
        if kind not in CONTENT_KINDS:
            raise InterfaceError("unknown interface content kind")
        if kind == "suggestion" and not suggestions_enabled:
            return None
        if not text or not accessible_label or not cue:
            raise InterfaceError(
                "content requires text, accessible label, and non-color cue"
            )
        return {
            "kind": kind,
            "text": text,
            "accessible_label": accessible_label,
            "non_color_cue": cue,
            "mode": mode,
        }

    def accessibility_contract(self, *, mode: str) -> dict[str, Any]:
        self._mode(mode)
        return {
            "same_core_workflows": True,
            "keyboard_operable": True,
            "screen_reader_state": True,
            "non_color_cues": True,
            "adjustable_text": True,
            "reduced_motion": True,
            "pointer_only_actions": False,
        }

    def print_workflow_screen(
        self,
        screen_id: str,
        presentation: Mapping[str, Any],
        *,
        mode: str = "simple",
    ) -> dict[str, Any]:
        """Expose every print stage through one mode-parity FORGE contract."""
        self._mode(mode)
        if screen_id not in PRINT_WORKFLOW_SCREENS:
            raise InterfaceError("unknown print workflow screen")
        item = deepcopy(dict(presentation))
        required = {
            "heading",
            "summary",
            "actions",
            "plain_language",
            "accessible_label",
            "non_color_cue",
            "can_upload",
            "can_start_print",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise InterfaceError(
                f"print workflow presentation missing: {', '.join(missing)}"
            )
        if item["plain_language"] is not True:
            raise InterfaceError("print workflow must use plain language")
        if item["can_upload"] is not False or item["can_start_print"] is not False:
            raise InterfaceError("interface presentation cannot grant authority")
        actions = item["actions"]
        if not isinstance(actions, list) or any(
            not isinstance(action, Mapping)
            or not action.get("id")
            or not action.get("label")
            for action in actions
        ):
            raise InterfaceError("workflow actions require identifiers and labels")
        return {
            "schema_version": "1.0.0",
            "interface": "forge",
            "separate_slicer_interface": False,
            "screen_id": screen_id,
            "mode": mode,
            "heading": item["heading"],
            "summary": item["summary"],
            "actions": deepcopy(actions),
            "accessible_label": item["accessible_label"],
            "non_color_cue": item["non_color_cue"],
            "keyboard_operable": True,
            "screen_reader_state": True,
            "core_workflow_parity": True,
            "can_upload": False,
            "can_start_print": False,
            "details": item,
        }

    def print_workflow_error(
        self,
        *,
        screen_id: str,
        reason: str,
        summary: str,
        affected_object: str,
        next_step: str,
        mode: str = "simple",
        safety_impact: str = "none",
    ) -> dict[str, Any]:
        """Return a mode-independent, actionable workflow error."""
        self._mode(mode)
        if screen_id not in PRINT_WORKFLOW_SCREENS:
            raise InterfaceError("unknown print workflow screen")
        result = self.error(
            reason=reason,
            summary=summary,
            affected_object=affected_object,
            next_step=next_step,
            safety_impact=safety_impact,
        )
        result.update(
            {
                "screen_id": screen_id,
                "mode": mode,
                "accessible_label": f"Error: {summary}",
                "non_color_cue": "error",
                "core_workflow_parity": True,
            }
        )
        return result

    def subscribe(
        self,
        client_id: str,
        event_types: list[str],
        *,
        authorized: bool,
    ) -> dict[str, Any]:
        if authorized is not True:
            raise InterfaceError("event subscription requires authorization")
        if len(event_types) != len(set(event_types)):
            raise InterfaceError("event types must be unique")
        self._subscriptions[client_id] = set(event_types)
        return {
            "client_id": client_id,
            "event_types": sorted(event_types),
            "observational_only": True,
            "grants_control_authority": False,
        }

    @staticmethod
    def error(
        *,
        reason: str,
        summary: str,
        affected_object: str,
        next_step: str,
        safety_impact: str = "none",
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "summary": summary,
                "reason": reason,
                "affected_object": affected_object,
                "safety_impact": safety_impact,
                "recommended_next_step": next_step,
            },
        }

    @staticmethod
    def _mode(mode: str) -> None:
        if mode not in INTERFACE_MODES:
            raise InterfaceError("unknown interface mode")
