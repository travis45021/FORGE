"""FAS-005 side-effect-free orchestration gate."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class ExecutiveError(ValueError):
    """Raised when an orchestration gate blocks execution."""


PIPELINE = (
    "receive_request", "validate_mission", "verify_authority", "gather_evidence",
    "evaluate_policies", "resolve_capabilities", "consult_ai",
    "perform_risk_analysis", "select_action", "record_decision", "execute",
    "observe_outcome", "update_mission",
)


class ForgeExecutive:
    """Build a bounded execution request from already verified inputs."""

    def prepare_execution(
        self,
        mission: Mapping[str, Any],
        authorization: Mapping[str, Any],
        capability: Mapping[str, Any],
    ) -> dict[str, Any]:
        if mission.get("state") != "approved":
            raise ExecutiveError("mission is not approved")
        if authorization.get("outcome") != "allow":
            raise ExecutiveError("authorization does not allow execution")
        decision = authorization.get("effective_action")
        if not decision:
            raise ExecutiveError("effective action is missing")
        requested_capability = mission["plan"][0]["capability_id"]
        if capability.get("capability_id") != requested_capability:
            raise ExecutiveError("resolved capability does not satisfy mission")
        return {
            "classification": "command",
            "event_type": "forge.decision.execution_requested",
            "correlation_id": mission["correlation_id"],
            "subject": capability["provider_id"],
            "payload": {
                "mission_id": mission["mission_id"],
                "decision_id": authorization.get("decision_id"),
                "authorization_id": authorization["evaluation_id"],
                "effective_action": deepcopy(decision),
            },
        }
