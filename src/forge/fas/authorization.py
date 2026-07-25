"""Deterministic reference evaluator for FAS-008.

This module is intentionally side-effect free. It evaluates a normalized
authorization request against a caller-supplied, versioned policy set. It does
not execute actions, persist decisions, verify cryptographic signatures, or
load policy from ambient process state.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from fnmatch import fnmatchcase
import hashlib
import json
from typing import Any, Iterable, Mapping


class EvaluationError(ValueError):
    """Raised when an authorization request or policy set is malformed."""


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise EvaluationError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise EvaluationError(f"invalid timestamp: {value}") from exc


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EvaluationError("request and policy values must be canonical JSON") from exc


def _digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


def _require(mapping: Mapping[str, Any], fields: Iterable[str], label: str) -> None:
    missing = [field for field in fields if field not in mapping]
    if missing:
        raise EvaluationError(f"{label} missing required fields: {', '.join(missing)}")


def _match_action(patterns: list[str], action_type: str) -> bool:
    return any(fnmatchcase(action_type, pattern) for pattern in patterns)


def _facts_match(expected: Mapping[str, Any], actual: Mapping[str, Any]) -> bool:
    return all(key in actual and actual[key] == value for key, value in expected.items())


def _approval_counts(
    approvals: list[Mapping[str, Any]], evaluated_at: datetime
) -> dict[str, int]:
    counts: dict[str, int] = {}
    seen_ids: set[str] = set()
    for approval in approvals:
        _require(
            approval,
            ("approval_id", "approval_type", "approved_at", "expires_at", "verified"),
            "approval",
        )
        approval_id = str(approval["approval_id"])
        if approval_id in seen_ids:
            continue
        seen_ids.add(approval_id)
        if approval["verified"] is not True:
            continue
        approved_at = _utc(str(approval["approved_at"]))
        expires_at = _utc(str(approval["expires_at"]))
        if approved_at <= evaluated_at < expires_at:
            approval_type = str(approval["approval_type"])
            counts[approval_type] = counts.get(approval_type, 0) + 1
    return counts


class AuthorizationEngine:
    """Evaluate FAS-008 policies with deny-overrides combining."""

    ENGINE_ID = "forge-service:fas-008-reference-evaluator"
    ENGINE_VERSION = "1.0.0"

    def evaluate(
        self,
        request: Mapping[str, Any],
        policies: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        request = deepcopy(dict(request))
        policies = [deepcopy(dict(policy)) for policy in policies]
        self._validate_request(request)
        for policy in policies:
            self._validate_policy(policy)

        evaluated_at = _utc(request["evaluated_at"])
        action = request["requested_action"]
        action_type = action["action_type"]
        facts = request["facts"]

        policy_set = sorted(
            policies,
            key=lambda item: (item["policy_id"], item["version"]),
        )
        policy_set_digest = _digest(policy_set)
        evaluation_id = "forge-authorization:" + hashlib.sha256(
            _canonical(
                {
                    "request_id": request["request_id"],
                    "idempotency_key": request["idempotency_key"],
                    "policy_set_digest": policy_set_digest,
                }
            )
        ).hexdigest()[:32]

        invariant_denial = self._invariant_denial(request)
        if invariant_denial:
            return self._result(
                evaluation_id,
                request,
                policy_set_digest,
                "deny",
                [invariant_denial],
            )

        applicable = [
            policy
            for policy in policy_set
            if policy["enabled"]
            and _match_action(policy["action_patterns"], action_type)
            and _facts_match(policy.get("when_facts", {}), facts)
        ]
        matched_refs = [
            {"id": policy["policy_id"], "version": policy["version"]}
            for policy in applicable
        ]

        denying = [policy for policy in applicable if policy["effect"] == "deny"]
        if denying:
            return self._result(
                evaluation_id,
                request,
                policy_set_digest,
                "deny",
                ["explicit_deny"],
                matched_refs=matched_refs,
            )

        allows = [policy for policy in applicable if policy["effect"] == "allow"]
        if not allows:
            return self._result(
                evaluation_id,
                request,
                policy_set_digest,
                "deny",
                ["no_applicable_allow_policy"],
                matched_refs=matched_refs,
            )

        candidate_failures: list[str] = []
        candidate_challenges: list[dict[str, Any]] = []
        for policy in sorted(allows, key=lambda item: -item["priority"]):
            outcome = self._evaluate_allow(request, policy, evaluated_at)
            if outcome["outcome"] == "allow":
                return self._result(
                    evaluation_id,
                    request,
                    policy_set_digest,
                    "allow",
                    outcome["reason_codes"],
                    effective_action=outcome["effective_action"],
                    matched_refs=matched_refs,
                    applied_constraints=outcome["applied_constraints"],
                    obligations=policy["obligations"],
                )
            if outcome["outcome"] == "challenge":
                candidate_challenges.append(outcome)
            else:
                candidate_failures.extend(outcome["reason_codes"])

        if candidate_challenges:
            challenge = candidate_challenges[0]
            return self._result(
                evaluation_id,
                request,
                policy_set_digest,
                "challenge",
                challenge["reason_codes"],
                matched_refs=matched_refs,
                missing_approvals=challenge["missing_approvals"],
            )

        return self._result(
            evaluation_id,
            request,
            policy_set_digest,
            "deny",
            sorted(set(candidate_failures)) or ["allow_policy_requirements_not_met"],
            matched_refs=matched_refs,
        )

    def _validate_request(self, request: Mapping[str, Any]) -> None:
        _require(
            request,
            (
                "request_id",
                "idempotency_key",
                "evaluated_at",
                "authorization_phase",
                "actor",
                "role",
                "readiness_level",
                "granted_scopes",
                "requested_action",
                "approvals",
                "facts",
                "decision_state",
            ),
            "authorization request",
        )
        if request["authorization_phase"] not in {"decision", "execution"}:
            raise EvaluationError("authorization_phase must be decision or execution")
        if not isinstance(request["readiness_level"], int) or not 0 <= request[
            "readiness_level"
        ] <= 5:
            raise EvaluationError("readiness_level must be an integer from 0 through 5")
        actor = request["actor"]
        _require(actor, ("actor_id", "actor_type", "version"), "actor")
        action = request["requested_action"]
        _require(action, ("action_type", "target_refs", "parameters"), "requested_action")
        _utc(request["evaluated_at"])

    def _validate_policy(self, policy: Mapping[str, Any]) -> None:
        _require(
            policy,
            (
                "policy_id",
                "version",
                "enabled",
                "priority",
                "effect",
                "action_patterns",
                "actor_types",
                "roles",
                "minimum_readiness_level",
                "maximum_readiness_level",
                "required_scopes",
                "required_approvals",
                "parameter_constraints",
                "obligations",
            ),
            "policy",
        )
        if policy["effect"] not in {"allow", "deny"}:
            raise EvaluationError("policy effect must be allow or deny")
        if not policy["action_patterns"]:
            raise EvaluationError("policy action_patterns cannot be empty")

    def _invariant_denial(self, request: Mapping[str, Any]) -> str | None:
        actor_type = request["actor"]["actor_type"]
        level = request["readiness_level"]
        facts = request["facts"]
        phase = request["authorization_phase"]

        if facts.get("sentinel_state") == "blocked":
            return "sentinel_block"
        if facts.get("ledger_integrity") != "verified":
            return "ledger_integrity_unverified"
        if level == 5 and actor_type != "admin":
            return "arl5_admin_only"
        if level in {2, 3, 4} and facts.get("restricted_arl_access") is not True:
            return "restricted_arl_unavailable"
        if phase == "execution":
            decision = request["decision_state"]
            if decision.get("disposition") != "approved":
                return "decision_not_approved"
            if decision.get("signature_verified") is not True:
                return "decision_signature_unverified"
            if decision.get("superseded") is True or decision.get("revoked") is True:
                return "decision_not_current"
        return None

    def _evaluate_allow(
        self,
        request: Mapping[str, Any],
        policy: Mapping[str, Any],
        evaluated_at: datetime,
    ) -> dict[str, Any]:
        actor_type = request["actor"]["actor_type"]
        if actor_type not in policy["actor_types"]:
            return {"outcome": "deny", "reason_codes": ["actor_type_not_granted"]}
        if request["role"] not in policy["roles"]:
            return {"outcome": "deny", "reason_codes": ["role_not_granted"]}
        if not (
            policy["minimum_readiness_level"]
            <= request["readiness_level"]
            <= policy["maximum_readiness_level"]
        ):
            return {"outcome": "deny", "reason_codes": ["readiness_level_not_granted"]}

        granted = set(request["granted_scopes"])
        required = set(policy["required_scopes"])
        if not required.issubset(granted):
            return {"outcome": "deny", "reason_codes": ["required_scope_missing"]}

        counts = _approval_counts(request["approvals"], evaluated_at)
        missing = []
        for requirement in policy["required_approvals"]:
            supplied = counts.get(requirement["approval_type"], 0)
            required_count = requirement["minimum_count"]
            if supplied < required_count:
                missing.append(
                    {
                        "approval_type": requirement["approval_type"],
                        "minimum_count": required_count,
                        "supplied_count": supplied,
                    }
                )
        if missing:
            return {
                "outcome": "challenge",
                "reason_codes": ["required_approval_missing"],
                "missing_approvals": missing,
            }

        effective_action = deepcopy(request["requested_action"])
        applied_constraints = []
        for constraint in policy["parameter_constraints"]:
            name = constraint["parameter"]
            if name not in effective_action["parameters"]:
                if constraint.get("required", False):
                    return {
                        "outcome": "deny",
                        "reason_codes": ["required_parameter_missing"],
                    }
                continue
            value = effective_action["parameters"][name]
            lower = constraint.get("minimum")
            upper = constraint.get("maximum")
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return {
                    "outcome": "deny",
                    "reason_codes": ["constrained_parameter_not_numeric"],
                }
            bounded = value
            if lower is not None and value < lower:
                bounded = lower
            if upper is not None and value > upper:
                bounded = upper
            if bounded != value:
                if constraint["on_violation"] == "reject":
                    return {
                        "outcome": "deny",
                        "reason_codes": ["parameter_outside_policy_bounds"],
                    }
                effective_action["parameters"][name] = bounded
                applied_constraints.append(
                    {
                        "parameter": name,
                        "requested_value": value,
                        "effective_value": bounded,
                        "policy_id": policy["policy_id"],
                    }
                )

        reason_codes = ["policy_allow"]
        if applied_constraints:
            reason_codes.append("effective_action_constrained")
        return {
            "outcome": "allow",
            "reason_codes": reason_codes,
            "effective_action": effective_action,
            "applied_constraints": applied_constraints,
        }

    def _result(
        self,
        evaluation_id: str,
        request: Mapping[str, Any],
        policy_set_digest: str,
        outcome: str,
        reason_codes: list[str],
        *,
        effective_action: Mapping[str, Any] | None = None,
        matched_refs: list[dict[str, str]] | None = None,
        missing_approvals: list[dict[str, Any]] | None = None,
        applied_constraints: list[dict[str, Any]] | None = None,
        obligations: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "evaluation_id": evaluation_id,
            "schema_version": "1.0.0",
            "request_id": request["request_id"],
            "idempotency_key": request["idempotency_key"],
            "evaluated_at": request["evaluated_at"],
            "engine": {
                "id": self.ENGINE_ID,
                "version": self.ENGINE_VERSION,
            },
            "policy_set_digest": policy_set_digest,
            "outcome": outcome,
            "reason_codes": reason_codes,
            "effective_action": deepcopy(effective_action),
            "matched_policy_refs": matched_refs or [],
            "missing_approvals": missing_approvals or [],
            "applied_constraints": applied_constraints or [],
            "obligations": obligations or [],
        }
