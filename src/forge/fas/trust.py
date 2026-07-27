"""Deterministic trust verification and Sentinel evidence boundaries for FAS-010.

Cryptographic algorithms are injected. The included HMAC helper is for tests and
examples only; production adapters should use approved asymmetric verification.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any

Verifier = Callable[[bytes, str, Mapping[str, Any]], bool]


class TrustError(ValueError):
    """Raised when a trust claim violates FAS-010."""


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
        raise TrustError("trust payload must be canonical JSON") from exc


def payload_digest(value: Any) -> str:
    """Return the canonical SHA-256 identity of a JSON-compatible value."""
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise TrustError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise TrustError(f"invalid timestamp: {value}") from exc


def development_hmac_signature(payload: Any, secret: str) -> str:
    """Create a non-production HMAC signature for examples and tests."""
    return hmac.new(
        secret.encode("utf-8"), _canonical(payload), hashlib.sha256
    ).hexdigest()


def development_hmac_verifier(
    payload: bytes, signature: str, key: Mapping[str, Any]
) -> bool:
    """Verify the explicit non-production ``hmac-sha256-test`` algorithm."""
    expected = hmac.new(
        key["verification_material"].encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


class TrustService:
    """In-memory FAS-010 reference trust service."""

    SERVICE_ID = "forge-service:fas-010-reference-trust"
    SERVICE_VERSION = "1.0.0"

    def __init__(self, verifiers: Mapping[str, Verifier] | None = None) -> None:
        self._verifiers = dict(verifiers or {})
        self._keys: dict[str, dict[str, Any]] = {}
        self._revocations: dict[str, dict[str, str]] = {}
        self._history: list[dict[str, Any]] = []

    def register_key(self, key: Mapping[str, Any]) -> str:
        """Register an immutable verification key and return its record digest."""
        candidate = deepcopy(dict(key))
        self._validate_key(candidate)
        key_id = candidate["key_id"]
        existing = self._keys.get(key_id)
        if existing is not None:
            if _canonical(existing) != _canonical(candidate):
                raise TrustError("registered key identifiers are immutable")
            return payload_digest(existing)

        predecessor = candidate["predecessor_key_id"]
        if predecessor is not None:
            prior = self._keys.get(predecessor)
            if prior is None:
                raise TrustError("predecessor key is not registered")
            if prior["subject_id"] != candidate["subject_id"]:
                raise TrustError("rotated keys must retain subject identity")
            if _utc(candidate["not_before"]) < _utc(prior["not_before"]):
                raise TrustError("successor cannot predate predecessor")

        self._keys[key_id] = candidate
        self._record("key_registered", key_id)
        return payload_digest(candidate)

    def revoke_key(
        self,
        key_id: str,
        *,
        revoked_at: str,
        reason: str,
        authority_verified: bool,
    ) -> dict[str, str]:
        """Record an effective revocation without deleting key history."""
        if key_id not in self._keys:
            raise TrustError(f"unknown key: {key_id}")
        if authority_verified is not True:
            raise TrustError("revocation requires verified governance authority")
        _utc(revoked_at)
        if not isinstance(reason, str) or len(reason.strip()) < 3:
            raise TrustError("revocation reason is required")
        record = {"revoked_at": revoked_at, "reason": reason.strip()}
        existing = self._revocations.get(key_id)
        if existing is not None and existing != record:
            raise TrustError("key revocation is immutable")
        self._revocations[key_id] = record
        self._record("key_revoked", key_id, record)
        return deepcopy(record)

    def verify_signature(
        self,
        payload: Any,
        envelope: Mapping[str, Any],
        *,
        subject_id: str,
        evaluated_at: str,
    ) -> dict[str, Any]:
        """Verify a signature claim and return a schema-valid attestation."""
        when = _utc(evaluated_at)
        claim = dict(envelope)
        required = {"key_id", "algorithm", "purpose", "signature"}
        missing = sorted(required - claim.keys())
        if missing:
            raise TrustError(f"signature envelope missing fields: {', '.join(missing)}")

        key = self._keys.get(claim["key_id"])
        if key is None:
            raise TrustError("signature key is not registered")
        if key["subject_id"] != subject_id:
            raise TrustError("signature key does not belong to claimed subject")
        if claim["algorithm"] != key["algorithm"]:
            raise TrustError("signature algorithm does not match key")
        if claim["purpose"] not in key["purposes"]:
            raise TrustError("signature purpose is not allowed by key")
        if not _utc(key["not_before"]) <= when < _utc(key["not_after"]):
            raise TrustError("key is outside its validity interval")
        revocation = self._revocations.get(key["key_id"])
        if revocation is not None and when >= _utc(revocation["revoked_at"]):
            raise TrustError("key was revoked at evaluation time")

        verifier = self._verifiers.get(key["algorithm"])
        if verifier is None:
            raise TrustError("no verifier is registered for key algorithm")
        if verifier(_canonical(payload), claim["signature"], key) is not True:
            raise TrustError("signature verification failed")

        digest = payload_digest(payload)
        attestation = {
            "attestation_id": "forge-attestation:"
            + hashlib.sha256(
                _canonical(
                    {
                        "key_id": key["key_id"],
                        "purpose": claim["purpose"],
                        "payload_digest": digest,
                        "evaluated_at": evaluated_at,
                    }
                )
            ).hexdigest()[:32],
            "schema_version": "1.0.0",
            "subject_id": subject_id,
            "key_id": key["key_id"],
            "algorithm": key["algorithm"],
            "purpose": claim["purpose"],
            "payload_digest": digest,
            "verifier": {"id": self.SERVICE_ID, "version": self.SERVICE_VERSION},
            "evaluated_at": evaluated_at,
            "verified": True,
            "reason_codes": ["signature_valid", "key_valid", "purpose_allowed"],
            "predecessor_key_id": key["predecessor_key_id"],
            "revocation": deepcopy(revocation),
        }
        self._record("signature_verified", key["key_id"], attestation)
        return attestation

    def verify_approval(
        self,
        approval: Mapping[str, Any],
        *,
        subject_digest: str,
        evaluated_at: str,
    ) -> dict[str, Any]:
        """Verify an approval bound to an exact subject digest and time window."""
        claim = deepcopy(dict(approval))
        required = {
            "approval_id",
            "approval_type",
            "approver_id",
            "subject_digest",
            "approved_at",
            "expires_at",
            "signature",
        }
        missing = sorted(required - claim.keys())
        if missing:
            raise TrustError(f"approval missing fields: {', '.join(missing)}")
        when = _utc(evaluated_at)
        if claim["subject_digest"] != subject_digest:
            raise TrustError("approval is bound to a different subject digest")
        if not _utc(claim["approved_at"]) <= when < _utc(claim["expires_at"]):
            raise TrustError("approval is outside its validity interval")

        signed_payload = {
            "approval_id": claim["approval_id"],
            "approval_type": claim["approval_type"],
            "approver_id": claim["approver_id"],
            "subject_digest": claim["subject_digest"],
            "approved_at": claim["approved_at"],
            "expires_at": claim["expires_at"],
        }
        attestation = self.verify_signature(
            signed_payload,
            claim["signature"],
            subject_id=claim["approver_id"],
            evaluated_at=evaluated_at,
        )
        if attestation["purpose"] != "forge.signature.approval":
            raise TrustError("approval must use approval signature purpose")
        return {
            "approval_id": claim["approval_id"],
            "approval_type": claim["approval_type"],
            "approved_at": claim["approved_at"],
            "expires_at": claim["expires_at"],
            "verified": True,
            "trust_attestation_id": attestation["attestation_id"],
        }

    def record_sentinel_evidence(self, evidence: Mapping[str, Any]) -> dict[str, Any]:
        """Validate Sentinel evidence without converting it into authority."""
        record = deepcopy(dict(evidence))
        required = {
            "evidence_id",
            "model_id",
            "model_version",
            "evaluated_at",
            "recommendation",
            "confidence",
            "evidence_refs",
            "limitations",
            "affected_scope",
        }
        missing = sorted(required - record.keys())
        if missing:
            raise TrustError(f"Sentinel evidence missing fields: {', '.join(missing)}")
        if record["recommendation"] not in {
            "allow_evidence",
            "challenge",
            "block",
            "quarantine",
        }:
            raise TrustError("invalid Sentinel recommendation")
        confidence = record["confidence"]
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            raise TrustError("Sentinel confidence must be between 0 and 1")
        _utc(record["evaluated_at"])
        if not record["evidence_refs"] or not record["limitations"]:
            raise TrustError("Sentinel evidence requires references and limitations")
        record["authoritative"] = False
        record["requires_executive_evaluation"] = True
        self._record("sentinel_evidence_recorded", record["model_id"], record)
        return record

    def key(self, key_id: str) -> dict[str, Any] | None:
        key = self._keys.get(key_id)
        return deepcopy(key) if key is not None else None

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def _validate_key(self, key: Mapping[str, Any]) -> None:
        required = {
            "key_id",
            "subject_id",
            "algorithm",
            "verification_material",
            "purposes",
            "not_before",
            "not_after",
            "predecessor_key_id",
            "status",
        }
        missing = sorted(required - key.keys())
        if missing:
            raise TrustError(f"key missing fields: {', '.join(missing)}")
        if key["status"] != "active":
            raise TrustError("new keys must be registered as active")
        if not isinstance(key["purposes"], list) or not key["purposes"]:
            raise TrustError("key must declare at least one purpose")
        if len(key["purposes"]) != len(set(key["purposes"])):
            raise TrustError("key purposes must be unique")
        if _utc(key["not_before"]) >= _utc(key["not_after"]):
            raise TrustError("key validity interval is empty")

    def _record(
        self,
        action: str,
        subject: str,
        detail: Mapping[str, Any] | None = None,
    ) -> None:
        self._history.append(
            {
                "action": action,
                "subject": subject,
                "detail": deepcopy(dict(detail or {})),
            }
        )
