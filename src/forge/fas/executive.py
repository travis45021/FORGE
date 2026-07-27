"""FAS-005 side-effect-free orchestration gate."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from typing import Any


class ExecutiveError(ValueError):
    """Raised when an orchestration gate blocks execution."""


PIPELINE = (
    "receive_request",
    "validate_mission",
    "verify_authority",
    "gather_evidence",
    "evaluate_policies",
    "resolve_capabilities",
    "consult_ai",
    "perform_risk_analysis",
    "select_action",
    "record_decision",
    "execute",
    "observe_outcome",
    "update_mission",
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

    def prepare_confirmed_artifact_execution(
        self,
        mission: Mapping[str, Any],
        job: Mapping[str, Any],
        acceptance: Mapping[str, Any],
        authorization: Mapping[str, Any],
        capability: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Bind accepted evidence and the fourth click to an Executive request."""
        if acceptance.get("ready_for_live_checks") is not True:
            raise ExecutiveError("slicer artifact is not accepted")
        if acceptance.get("preflight_verified") is not True:
            raise ExecutiveError("slicer acceptance lacks deterministic preflight")
        if (
            acceptance.get("final_confirmation_required") is not True
            or acceptance.get("can_upload") is not False
            or acceptance.get("can_start_print") is not False
        ):
            raise ExecutiveError("slicer acceptance must remain non-authoritative")
        artifact_digest = acceptance.get("artifact_digest")
        if not self._digest(artifact_digest):
            raise ExecutiveError("accepted artifact digest is invalid")
        if job.get("state") != "upload_pending" or job.get("click_count") != 3:
            raise ExecutiveError("job has not passed the fourth-click gate")
        if job.get("artifact_digest") != artifact_digest:
            raise ExecutiveError("job and accepted artifact do not match")
        if job.get("provider_id") != capability.get("provider_id"):
            raise ExecutiveError("job and capability provider do not match")
        token = job.get("confirmation_token")
        if (
            not job.get("final_confirmed_by")
            or not isinstance(token, str)
            or len(token) < 32
        ):
            raise ExecutiveError("fresh final-confirmation evidence is required")
        context = mission.get("context")
        if (
            not isinstance(context, Mapping)
            or context.get("job_id") != job.get("job_id")
            or context.get("artifact_digest") != artifact_digest
        ):
            raise ExecutiveError("Mission context does not match the confirmed job")

        request = self.prepare_execution(mission, authorization, capability)
        request["payload"].update(
            {
                "job_id": job["job_id"],
                "artifact_digest": artifact_digest,
                "confirmation_token_digest": sha256(token.encode("utf-8")).hexdigest(),
                "final_confirmation_verified": True,
                "artifact_preflight_verified": True,
                "physical_dispatch_allowed": False,
                "requires_runtime_dispatcher": True,
            }
        )
        return request

    @staticmethod
    def _digest(value: Any) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )
