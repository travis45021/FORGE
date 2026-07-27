"""Recorded execution contexts and expiring resource leases for FAS-022."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any


class RuntimeError(ValueError):
    """Raised when runtime execution violates FAS-022."""


STATES = {
    "created",
    "preparing",
    "ready",
    "running",
    "waiting",
    "paused",
    "recovering",
    "verifying",
    "completed",
    "failed",
    "cancelled",
    "aborted",
}
TERMINAL = {"completed", "failed", "cancelled", "aborted"}
TRANSITIONS = {
    "created": {"preparing", "cancelled"},
    "preparing": {"ready", "failed", "cancelled"},
    "ready": {"running", "cancelled"},
    "running": {"waiting", "paused", "recovering", "verifying", "failed", "aborted"},
    "waiting": {"running", "paused", "failed", "cancelled"},
    "paused": {"running", "recovering", "cancelled", "aborted"},
    "recovering": {"ready", "paused", "failed", "aborted"},
    "verifying": {"completed", "failed"},
}


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RuntimeError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RuntimeError(f"invalid timestamp: {value}") from exc


class ForgeRuntime:
    """Local v1 runtime; it executes no work outside a recorded context."""

    def __init__(self) -> None:
        self._contexts: dict[str, dict[str, Any]] = {}
        self._leases: dict[str, dict[str, Any]] = {}
        self._consumed_confirmation_tokens: set[str] = set()
        self._history: list[dict[str, Any]] = []

    def create_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(context))
        self._validate_context(item)
        context_id = item["context_id"]
        if context_id in self._contexts:
            raise RuntimeError("execution context identity is immutable")
        parent_id = item["parent_context_id"]
        if parent_id is not None:
            parent = self._require_context(parent_id)
            for field in ("allowed_capabilities", "target_objects", "data_access"):
                if not set(item[field]) <= set(parent[field]):
                    raise RuntimeError("child context cannot broaden parent boundaries")
            if item["automation_level"] != parent["automation_level"]:
                raise RuntimeError("child context cannot change automation authority")
            if item["authority_reference"] != parent["authority_reference"]:
                raise RuntimeError("child context cannot replace authority")
        self._contexts[context_id] = item
        self._record("runtime.context.created", context_id, "context_recorded")
        return deepcopy(item)

    def transition(
        self,
        context_id: str,
        state: str,
        *,
        trigger: str,
        authority_reference: str,
    ) -> dict[str, Any]:
        item = self._require_context(context_id)
        if state not in STATES:
            raise RuntimeError("unknown runtime state")
        if state not in TRANSITIONS.get(item["state"], set()):
            raise RuntimeError(
                f"invalid runtime transition: {item['state']} -> {state}"
            )
        if authority_reference != item["authority_reference"]:
            raise RuntimeError("state transition authority does not match context")
        item["state"] = state
        item["reason"] = trigger
        if state in TERMINAL:
            self.release_context(context_id, reason=f"context_{state}")
        self._record("runtime.context.transitioned", context_id, trigger)
        return deepcopy(item)

    def reserve(
        self,
        context_id: str,
        resource_id: str,
        *,
        mode: str,
        acquired_at: str,
        expires_at: str,
    ) -> dict[str, Any]:
        context = self._require_context(context_id)
        acquired = _utc(acquired_at)
        expiry = _utc(expires_at)
        if expiry <= acquired:
            raise RuntimeError("lease expiry must follow acquisition")
        if resource_id not in context["reserved_resources"]:
            raise RuntimeError("resource is outside execution context")
        if mode not in {"exclusive", "shared_read", "shared_limited"}:
            raise RuntimeError("unknown resource mode")
        for lease in self._leases.values():
            if (
                lease["resource_id"] == resource_id
                and lease["state"] == "active"
                and _utc(lease["expires_at"]) > acquired
                and (mode == "exclusive" or lease["mode"] == "exclusive")
            ):
                raise RuntimeError("resource has an incompatible active lease")
        lease_id = (
            f"forge-lease:{context_id.split(':')[-1]}:{resource_id.split(':')[-1]}"
        )
        lease = {
            "lease_id": lease_id,
            "context_id": context_id,
            "resource_id": resource_id,
            "mode": mode,
            "acquired_at": acquired_at,
            "expires_at": expires_at,
            "state": "active",
        }
        self._leases[lease_id] = lease
        self._record("runtime.resource.leased", context_id, resource_id)
        return deepcopy(lease)

    def renew_lease(
        self,
        lease_id: str,
        *,
        renewed_at: str,
        expires_at: str,
        authority_verified: bool,
    ) -> dict[str, Any]:
        lease = self._require_lease(lease_id)
        now = _utc(renewed_at)
        expiry = _utc(expires_at)
        if authority_verified is not True:
            raise RuntimeError("lease renewal requires verified authority")
        if lease["state"] != "active" or now >= _utc(lease["expires_at"]):
            raise RuntimeError("expired leases cannot be renewed")
        if expiry <= now:
            raise RuntimeError("renewed lease must expire in the future")
        lease["expires_at"] = expires_at
        return deepcopy(lease)

    def expire_leases(self, *, evaluated_at: str) -> list[dict[str, Any]]:
        now = _utc(evaluated_at)
        expired = []
        for lease in self._leases.values():
            if lease["state"] == "active" and now >= _utc(lease["expires_at"]):
                lease["state"] = "expired"
                context = self._require_context(lease["context_id"])
                if context["state"] not in TERMINAL:
                    context["state"] = "recovering"
                    context["reason"] = "resource_lease_expired"
                expired.append(deepcopy(lease))
                self._record(
                    "runtime.resource.lease_expired",
                    lease["context_id"],
                    lease["resource_id"],
                )
        return expired

    def dispatch(
        self,
        context_id: str,
        command: Mapping[str, Any],
        *,
        evaluated_at: str,
        provider_healthy: bool,
        current_state_allows: bool,
    ) -> dict[str, Any]:
        context = self._require_context(context_id)
        claim = deepcopy(dict(command))
        required = {
            "command_id",
            "context_id",
            "capability_id",
            "provider_id",
            "resource_ids",
            "expires_at",
            "verification_passed",
        }
        missing = sorted(required - claim.keys())
        if missing:
            raise RuntimeError(f"command missing fields: {', '.join(missing)}")
        now = _utc(evaluated_at)
        if context["state"] not in {"ready", "running"}:
            raise RuntimeError("context state does not permit dispatch")
        if claim["context_id"] != context_id:
            raise RuntimeError("command belongs to a different context")
        if context["authorization_verified"] is not True:
            raise RuntimeError("context authority is not verified")
        providers = {
            (item["capability_id"], item["provider_id"])
            for item in context["resolved_capabilities"]
        }
        if (claim["capability_id"], claim["provider_id"]) not in providers:
            raise RuntimeError("provider is not resolved in context")
        if provider_healthy is not True:
            raise RuntimeError("provider is not healthy")
        if claim["verification_passed"] is not True:
            raise RuntimeError("verification gate did not pass")
        if not current_state_allows:
            raise RuntimeError("current state does not permit command")
        if now >= _utc(claim["expires_at"]):
            raise RuntimeError("command expired")
        for resource_id in claim["resource_ids"]:
            if not self._has_active_lease(context_id, resource_id, now):
                raise RuntimeError("required resource lease is not active")
        self._record("runtime.command.dispatched", context_id, claim["command_id"])
        return {
            "command_id": claim["command_id"],
            "context_id": context_id,
            "status": "dispatched",
            "physical_outcome_confirmed": False,
        }

    def dispatch_artifact_upload(
        self,
        context_id: str,
        prepared: Mapping[str, Any],
        *,
        command_id: str,
        resource_ids: list[str],
        expires_at: str,
        evaluated_at: str,
        provider_healthy: bool,
        current_state_allows: bool,
        historical_replay: bool = False,
    ) -> dict[str, Any]:
        """Dispatch a fourth-click upload handoff through the recorded runtime."""
        handoff = deepcopy(dict(prepared))
        if historical_replay:
            raise RuntimeError("historical replay cannot dispatch an artifact upload")
        if handoff.get("historical_replay_allowed") is not False:
            raise RuntimeError(
                "upload handoff must explicitly prohibit historical replay"
            )
        if handoff.get("physical_dispatch_allowed") is not False:
            raise RuntimeError("upload handoff must not self-authorize dispatch")
        if handoff.get("requires_runtime_dispatcher") is not True:
            raise RuntimeError("upload handoff must require the runtime dispatcher")
        if handoff.get("fourth_click_satisfied") is not True:
            raise RuntimeError("upload handoff requires the fourth user click")
        if handoff.get("artifact_preflight_verified") is not True:
            raise RuntimeError("upload handoff requires deterministic preflight")
        if handoff.get("artifact_pair_preflight_verified") is not True:
            raise RuntimeError("upload handoff requires coordinated pair preflight")
        if not handoff.get("comparison_id"):
            raise RuntimeError("upload handoff requires reviewed comparison identity")
        if not handoff.get("comparison_reviewed_by") or not handoff.get(
            "comparison_reviewed_at"
        ):
            raise RuntimeError("upload handoff requires click-three attribution")
        if not handoff.get("confirmed_by") or not handoff.get("confirmed_at"):
            raise RuntimeError("upload handoff requires fourth-click attribution")
        reviewed_at = _utc(handoff["comparison_reviewed_at"])
        confirmed_at = _utc(handoff["confirmed_at"])
        confirmation_expires_at = _utc(handoff.get("confirmation_expires_at"))
        live_checks_checked_at = _utc(handoff.get("live_checks_checked_at"))
        live_checks_expires_at = _utc(handoff.get("live_checks_expires_at"))
        dispatch_at = _utc(evaluated_at)
        if reviewed_at > confirmed_at:
            raise RuntimeError("click-three review occurred after final confirmation")
        if confirmed_at > dispatch_at:
            raise RuntimeError("final confirmation cannot be in the dispatch future")
        if confirmation_expires_at <= confirmed_at:
            raise RuntimeError("final confirmation expiry is invalid")
        if dispatch_at >= confirmation_expires_at:
            raise RuntimeError("final confirmation expired before dispatch")
        if live_checks_checked_at > confirmed_at:
            raise RuntimeError("live printer checks occurred after final confirmation")
        if dispatch_at >= live_checks_expires_at:
            raise RuntimeError("live printer checks expired before dispatch")
        confirmation_token = handoff.get("confirmation_token")
        if not isinstance(confirmation_token, str) or len(confirmation_token) < 32:
            raise RuntimeError("upload handoff requires a fresh confirmation token")
        if confirmation_token in self._consumed_confirmation_tokens:
            raise RuntimeError("final-confirmation token has already been consumed")
        artifact_digest = handoff.get("artifact_digest")
        if (
            not isinstance(artifact_digest, str)
            or len(artifact_digest) != 64
            or any(character not in "0123456789abcdef" for character in artifact_digest)
        ):
            raise RuntimeError("upload artifact digest must be lowercase SHA-256")
        for field in (
            "comparison_evidence_digest",
            "live_checks_evidence_digest",
            "input_digest",
            "profile_digest",
            "engine_source_digest",
            "engine_build_digest",
        ):
            value = handoff.get(field)
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise RuntimeError(
                    f"upload {field.replace('_', ' ')} must be lowercase SHA-256"
                )
        result = self.dispatch(
            context_id,
            {
                "command_id": command_id,
                "context_id": context_id,
                "capability_id": "artifact.upload",
                "provider_id": handoff.get("provider_id"),
                "resource_ids": resource_ids,
                "expires_at": expires_at,
                "verification_passed": True,
            },
            evaluated_at=evaluated_at,
            provider_healthy=provider_healthy,
            current_state_allows=current_state_allows,
        )
        self._consumed_confirmation_tokens.add(confirmation_token)
        result.update(
            {
                "job_id": handoff.get("job_id"),
                "artifact_digest": artifact_digest,
                "comparison_id": handoff.get("comparison_id"),
                "comparison_evidence_digest": handoff["comparison_evidence_digest"],
                "comparison_reviewed_by": handoff["comparison_reviewed_by"],
                "comparison_reviewed_at": handoff["comparison_reviewed_at"],
                "input_digest": handoff["input_digest"],
                "profile_digest": handoff["profile_digest"],
                "engine_source_digest": handoff["engine_source_digest"],
                "engine_build_digest": handoff["engine_build_digest"],
                "confirmed_by": handoff.get("confirmed_by"),
                "confirmed_at": handoff.get("confirmed_at"),
                "confirmation_expires_at": handoff.get("confirmation_expires_at"),
                "live_checks_checked_at": handoff.get("live_checks_checked_at"),
                "live_checks_expires_at": handoff.get("live_checks_expires_at"),
                "live_checks_evidence_digest": handoff["live_checks_evidence_digest"],
            }
        )
        return result

    def assess_restart(
        self,
        context_id: str,
        *,
        physical_work: bool,
        provider_state_verified: bool,
        hardware_state_verified: bool,
        safety_verified: bool,
        authority_reverified: bool,
        leases_reacquired: bool,
    ) -> dict[str, Any]:
        context = self._require_context(context_id)
        context["state"] = "recovering"
        checks = {
            "provider_state_verified": provider_state_verified,
            "hardware_state_verified": hardware_state_verified,
            "safety_verified": safety_verified,
            "authority_reverified": authority_reverified,
            "leases_reacquired": leases_reacquired,
        }
        if physical_work and not all(checks.values()):
            context["state"] = "paused"
            context["reason"] = "restart_requires_verified_recovery"
            disposition = "do_not_resume"
        elif all(checks.values()):
            context["state"] = "ready"
            context["reason"] = "restart_recovery_verified"
            disposition = "eligible_for_scheduler_resume"
        else:
            context["state"] = "paused"
            context["reason"] = "restart_checks_incomplete"
            disposition = "do_not_resume"
        self._record("runtime.restart.assessed", context_id, disposition)
        return {
            "context_id": context_id,
            "disposition": disposition,
            "state": context["state"],
            "checks": checks,
        }

    def release_context(self, context_id: str, *, reason: str) -> None:
        self._require_context(context_id)
        for lease in self._leases.values():
            if lease["context_id"] == context_id and lease["state"] == "active":
                lease["state"] = "released"
        self._record("runtime.resources.released", context_id, reason)

    def context(self, context_id: str) -> dict[str, Any] | None:
        item = self._contexts.get(context_id)
        return deepcopy(item) if item else None

    def leases(self, context_id: str | None = None) -> list[dict[str, Any]]:
        return [
            deepcopy(item)
            for item in self._leases.values()
            if context_id is None or item["context_id"] == context_id
        ]

    def health(self) -> dict[str, Any]:
        return {
            "state": "ready",
            "active_contexts": sum(
                item["state"] not in TERMINAL for item in self._contexts.values()
            ),
            "active_leases": sum(
                item["state"] == "active" for item in self._leases.values()
            ),
        }

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def _validate_context(self, item: Mapping[str, Any]) -> None:
        required = {
            "context_id",
            "mission_id",
            "parent_context_id",
            "authority_reference",
            "authorization_verified",
            "policy_snapshot",
            "automation_level",
            "target_objects",
            "allowed_capabilities",
            "resolved_capabilities",
            "reserved_resources",
            "configuration_snapshot",
            "verification_packet",
            "data_access",
            "time_limit_seconds",
            "cost_limit",
            "correlation_id",
            "started_at",
            "state",
            "reason",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise RuntimeError(f"context missing fields: {', '.join(missing)}")
        if item["state"] != "created":
            raise RuntimeError("new contexts must begin created")
        _utc(item["started_at"])
        if not isinstance(item["authorization_verified"], bool):
            raise RuntimeError("authorization_verified must be boolean")
        for field in (
            "target_objects",
            "allowed_capabilities",
            "reserved_resources",
            "data_access",
        ):
            if not isinstance(item[field], list) or len(item[field]) != len(
                set(item[field])
            ):
                raise RuntimeError(f"{field} must be a unique list")
        if item["time_limit_seconds"] <= 0:
            raise RuntimeError("context time limit must be positive")

    def _has_active_lease(
        self, context_id: str, resource_id: str, when: datetime
    ) -> bool:
        return any(
            lease["context_id"] == context_id
            and lease["resource_id"] == resource_id
            and lease["state"] == "active"
            and when < _utc(lease["expires_at"])
            for lease in self._leases.values()
        )

    def _require_context(self, context_id: str) -> dict[str, Any]:
        try:
            return self._contexts[context_id]
        except KeyError as exc:
            raise RuntimeError(f"unknown context: {context_id}") from exc

    def _require_lease(self, lease_id: str) -> dict[str, Any]:
        try:
            return self._leases[lease_id]
        except KeyError as exc:
            raise RuntimeError(f"unknown lease: {lease_id}") from exc

    def _record(self, event_type: str, context_id: str, reason: str) -> None:
        self._history.append(
            {"event_type": event_type, "context_id": context_id, "reason": reason}
        )
