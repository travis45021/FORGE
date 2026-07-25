"""Deterministic verification packets and assurance gates for FAS-018."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from typing import Any, Mapping


class AssuranceError(ValueError):
    """Raised when an assurance claim violates FAS-018."""


CLAIM_STATES = {
    "observation",
    "hypothesis",
    "candidate",
    "tested",
    "verified_recommendation",
    "authorized_action",
    "measured_outcome",
}

CLASS_CHECKS = {
    "A0": {"source", "timestamp"},
    "A1": {"source", "timestamp", "context", "applicability"},
    "A2": {
        "source", "timestamp", "context", "applicability", "capability",
        "compatibility", "evidence_quality", "recovery",
    },
    "A3": {
        "source", "timestamp", "context", "applicability", "capability",
        "compatibility", "evidence_quality", "recovery", "authority",
        "live_state", "safety", "monitoring",
    },
    "A4": {
        "source", "timestamp", "context", "applicability", "capability",
        "compatibility", "evidence_quality", "recovery", "authority",
        "live_state", "safety", "monitoring", "deterministic_safety",
        "strong_evidence", "explicit_constraints",
        "conservative_authorization",
    },
}


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AssuranceError("assurance value must be canonical JSON") from exc


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise AssuranceError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise AssuranceError(f"invalid timestamp: {value}") from exc


def context_fingerprint(context: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(context)).hexdigest()}"


class AssuranceService:
    """Reference evaluator that verifies evidence separately from authority."""

    def __init__(self) -> None:
        self._packets: dict[str, dict[str, Any]] = {}
        self._outcomes: list[dict[str, Any]] = []

    def evaluate(
        self,
        packet: Mapping[str, Any],
        *,
        current_context: Mapping[str, Any],
        evaluated_at: str,
        authorization_verified: bool = False,
    ) -> dict[str, Any]:
        candidate = deepcopy(dict(packet))
        self._validate(candidate)
        when = _utc(evaluated_at)
        if candidate["assurance_class"] == "A5":
            raise AssuranceError("A5 delegated autonomy remains future-gated")
        required = CLASS_CHECKS[candidate["assurance_class"]]
        declared = set(candidate["required_checks"])
        if not required <= declared:
            missing = sorted(required - declared)
            raise AssuranceError(
                f"assurance class missing required checks: {', '.join(missing)}"
            )
        if candidate["context_fingerprint"] != context_fingerprint(current_context):
            return self._result(candidate, "blocked", "context_changed")
        if candidate["expires_at"] is not None and when >= _utc(
            candidate["expires_at"]
        ):
            return self._result(candidate, "blocked", "verification_expired")
        completed = set(candidate["completed_checks"])
        failed = set(candidate["failed_checks"])
        waived = set(candidate["waived_checks"])
        if failed:
            return self._result(candidate, "blocked", "required_check_failed")
        if not declared <= completed | waived:
            return self._result(candidate, "incomplete", "checks_incomplete")
        if candidate["assurance_class"] == "A4" and waived & {
            "safety", "deterministic_safety", "conservative_authorization"
        }:
            raise AssuranceError("safety-critical checks cannot be waived")
        if waived and not candidate["waiver"]:
            raise AssuranceError("waived checks require a governed waiver record")

        requested_state = candidate["claim_state"]
        if requested_state == "authorized_action":
            if candidate["assurance_class"] not in {"A3", "A4"}:
                raise AssuranceError("authorized actions require A3 or A4")
            if authorization_verified is not True:
                return self._result(
                    candidate, "verified", "authority_not_verified",
                    claim_state="verified_recommendation",
                )
        elif requested_state == "measured_outcome":
            raise AssuranceError("measured outcomes require outcome recording")

        result = self._result(candidate, "verified", "verification_passed")
        self._packets[candidate["verification_id"]] = deepcopy(result)
        return result

    def record_outcome(
        self,
        verification_id: str,
        *,
        measured_at: str,
        success: bool,
        measurements: Mapping[str, Any],
        evidence_refs: list[str],
    ) -> dict[str, Any]:
        packet = self._packets.get(verification_id)
        if packet is None or packet["disposition"] != "verified":
            raise AssuranceError("outcome requires a verified packet")
        _utc(measured_at)
        if not evidence_refs:
            raise AssuranceError("measured outcomes require evidence")
        outcome = {
            "verification_id": verification_id,
            "claim_state": "measured_outcome",
            "measured_at": measured_at,
            "success": success,
            "measurements": deepcopy(dict(measurements)),
            "evidence_refs": deepcopy(evidence_refs),
            "requires_revalidation": not success,
        }
        self._outcomes.append(outcome)
        return deepcopy(outcome)

    def packet(self, verification_id: str) -> dict[str, Any] | None:
        packet = self._packets.get(verification_id)
        return deepcopy(packet) if packet else None

    def _validate(self, packet: Mapping[str, Any]) -> None:
        required = {
            "verification_id", "subject_id", "claim_state", "assurance_class",
            "context_fingerprint", "required_checks", "completed_checks",
            "failed_checks", "waived_checks", "evidence_refs", "assumptions",
            "uncertainties", "applicability_limits", "confidence",
            "verifier_versions", "expires_at", "revalidate_when", "waiver",
        }
        missing = sorted(required - packet.keys())
        if missing:
            raise AssuranceError(f"packet missing fields: {', '.join(missing)}")
        if packet["claim_state"] not in CLAIM_STATES:
            raise AssuranceError("unknown claim state")
        if packet["assurance_class"] not in {*CLASS_CHECKS, "A5"}:
            raise AssuranceError("unknown assurance class")
        confidence = packet["confidence"]
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            raise AssuranceError("confidence must be between zero and one")
        if not packet["evidence_refs"]:
            raise AssuranceError("verification requires evidence")
        for field in (
            "required_checks", "completed_checks", "failed_checks",
            "waived_checks", "evidence_refs", "revalidate_when",
        ):
            if not isinstance(packet[field], list) or len(packet[field]) != len(
                set(packet[field])
            ):
                raise AssuranceError(f"{field} must be a unique list")
        declared = set(packet["required_checks"])
        for field in ("completed_checks", "failed_checks", "waived_checks"):
            if not set(packet[field]) <= declared:
                raise AssuranceError(f"{field} contains undeclared checks")
        if packet["expires_at"] is not None:
            _utc(packet["expires_at"])

    @staticmethod
    def _result(
        packet: Mapping[str, Any],
        disposition: str,
        reason_code: str,
        *,
        claim_state: str | None = None,
    ) -> dict[str, Any]:
        return {
            "verification_id": packet["verification_id"],
            "subject_id": packet["subject_id"],
            "assurance_class": packet["assurance_class"],
            "claim_state": claim_state or packet["claim_state"],
            "disposition": disposition,
            "reason_code": reason_code,
            "confidence": packet["confidence"],
            "uncertainties": deepcopy(packet["uncertainties"]),
            "applicability_limits": deepcopy(packet["applicability_limits"]),
            "context_fingerprint": packet["context_fingerprint"],
        }
