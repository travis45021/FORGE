"""Behavior and schema tests for FAS-010 trust verification."""

from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.trust import (
    TrustError,
    TrustService,
    development_hmac_signature,
    development_hmac_verifier,
    payload_digest,
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas010TrustTests(unittest.TestCase):
    def setUp(self) -> None:
        self.key = load_json(
            ROOT / "examples" / "fas" / "trust-key-release.example.json"
        )
        self.service = TrustService({"hmac-sha256-test": development_hmac_verifier})
        self.service.register_key(self.key)
        self.payload = {
            "release_id": "forge-release:0.10.0",
            "content_digest": "sha256:" + "a" * 64,
        }

    def envelope(
        self,
        payload: dict | None = None,
        purpose: str = "forge.signature.release",
    ) -> dict:
        return {
            "key_id": self.key["key_id"],
            "algorithm": self.key["algorithm"],
            "purpose": purpose,
            "signature": development_hmac_signature(
                payload or self.payload, self.key["verification_material"]
            ),
        }

    def verify(self, payload: dict | None = None, **changes: str) -> dict:
        envelope = {**self.envelope(payload), **changes}
        return self.service.verify_signature(
            payload or self.payload,
            envelope,
            subject_id=self.key["subject_id"],
            evaluated_at="2026-07-25T20:00:00Z",
        )

    def test_valid_signature_returns_deterministic_attestation(self) -> None:
        first = self.verify()
        second = self.verify()
        self.assertTrue(first["verified"])
        self.assertEqual(payload_digest(self.payload), first["payload_digest"])
        self.assertEqual(first["attestation_id"], second["attestation_id"])
        self.assertEqual(
            ["signature_valid", "key_valid", "purpose_allowed"], first["reason_codes"]
        )

    def test_tampered_payload_is_rejected(self) -> None:
        envelope = self.envelope()
        changed = {**self.payload, "content_digest": "sha256:" + "b" * 64}
        with self.assertRaisesRegex(TrustError, "verification failed"):
            self.service.verify_signature(
                changed,
                envelope,
                subject_id=self.key["subject_id"],
                evaluated_at="2026-07-25T20:00:00Z",
            )

    def test_wrong_subject_algorithm_and_purpose_fail_closed(self) -> None:
        cases = (
            ({"subject_id": "community-project:custom"}, "claimed subject"),
            ({"algorithm": "ed25519"}, "algorithm"),
            ({"purpose": "forge.signature.approval"}, "purpose"),
        )
        for changes, message in cases:
            with self.subTest(changes=changes):
                envelope = {
                    **self.envelope(),
                    **{
                        key: value
                        for key, value in changes.items()
                        if key != "subject_id"
                    },
                }
                with self.assertRaisesRegex(TrustError, message):
                    self.service.verify_signature(
                        self.payload,
                        envelope,
                        subject_id=changes.get("subject_id", self.key["subject_id"]),
                        evaluated_at="2026-07-25T20:00:00Z",
                    )

    def test_validity_interval_and_revocation_are_enforced(self) -> None:
        for evaluated_at in (
            "2026-07-24T23:59:59Z",
            "2027-07-25T00:00:00Z",
        ):
            with (
                self.subTest(evaluated_at=evaluated_at),
                self.assertRaisesRegex(TrustError, "validity interval"),
            ):
                self.service.verify_signature(
                    self.payload,
                    self.envelope(),
                    subject_id=self.key["subject_id"],
                    evaluated_at=evaluated_at,
                )
        self.service.revoke_key(
            self.key["key_id"],
            revoked_at="2026-08-01T00:00:00Z",
            reason="Signing material compromised",
            authority_verified=True,
        )
        self.service.verify_signature(
            self.payload,
            self.envelope(),
            subject_id=self.key["subject_id"],
            evaluated_at="2026-07-31T23:59:59Z",
        )
        with self.assertRaisesRegex(TrustError, "revoked"):
            self.service.verify_signature(
                self.payload,
                self.envelope(),
                subject_id=self.key["subject_id"],
                evaluated_at="2026-08-01T00:00:00Z",
            )

    def test_key_and_revocation_records_are_immutable(self) -> None:
        changed = deepcopy(self.key)
        changed["not_after"] = "2028-07-25T00:00:00Z"
        with self.assertRaisesRegex(TrustError, "immutable"):
            self.service.register_key(changed)
        with self.assertRaisesRegex(TrustError, "governance authority"):
            self.service.revoke_key(
                self.key["key_id"],
                revoked_at="2026-08-01T00:00:00Z",
                reason="Compromised",
                authority_verified=False,
            )

    def test_rotation_preserves_subject_and_lineage(self) -> None:
        successor = {
            **self.key,
            "key_id": "forge-key:release-2027-b",
            "verification_material": "development-only-secret-b",
            "not_before": "2027-01-01T00:00:00Z",
            "not_after": "2028-01-01T00:00:00Z",
            "predecessor_key_id": self.key["key_id"],
        }
        self.service.register_key(successor)
        self.assertEqual(
            self.key["key_id"],
            self.service.key(successor["key_id"])["predecessor_key_id"],
        )
        invalid = {**successor, "key_id": "forge-key:foreign-2027"}
        invalid["subject_id"] = "community-project:custom"
        with self.assertRaisesRegex(TrustError, "retain subject"):
            self.service.register_key(invalid)

    def test_signed_approval_binds_exact_digest_and_expiry(self) -> None:
        approver_key = {
            **self.key,
            "key_id": "forge-key:architect-2026",
            "subject_id": "forge-user:architect",
            "purposes": ["forge.signature.approval"],
        }
        self.service.register_key(approver_key)
        signed = {
            "approval_id": "forge-approval:fas010",
            "approval_type": "forge.approval.architect",
            "approver_id": approver_key["subject_id"],
            "subject_digest": payload_digest(self.payload),
            "approved_at": "2026-07-25T19:00:00Z",
            "expires_at": "2026-07-26T19:00:00Z",
        }
        approval = {
            **signed,
            "signature": {
                "key_id": approver_key["key_id"],
                "algorithm": approver_key["algorithm"],
                "purpose": "forge.signature.approval",
                "signature": development_hmac_signature(
                    signed, approver_key["verification_material"]
                ),
            },
        }
        result = self.service.verify_approval(
            approval,
            subject_digest=signed["subject_digest"],
            evaluated_at="2026-07-25T20:00:00Z",
        )
        self.assertTrue(result["verified"])
        with self.assertRaisesRegex(TrustError, "different subject digest"):
            self.service.verify_approval(
                approval,
                subject_digest="sha256:" + "0" * 64,
                evaluated_at="2026-07-25T20:00:00Z",
            )
        with self.assertRaisesRegex(TrustError, "validity interval"):
            self.service.verify_approval(
                approval,
                subject_digest=signed["subject_digest"],
                evaluated_at="2026-07-26T19:00:00Z",
            )

    def test_sentinel_evidence_is_never_authority(self) -> None:
        evidence = self.service.record_sentinel_evidence(
            {
                "evidence_id": "forge-evidence:sentinel-1",
                "model_id": "forge-model:sentinel-local",
                "model_version": "1.0.0",
                "evaluated_at": "2026-07-25T20:00:00Z",
                "recommendation": "challenge",
                "confidence": 0.72,
                "evidence_refs": ["forge-evidence:scanner-1"],
                "limitations": ["Novel custom firmware has limited history"],
                "affected_scope": ["forge-plugin:community-driver"],
            }
        )
        self.assertFalse(evidence["authoritative"])
        self.assertTrue(evidence["requires_executive_evaluation"])

    def test_custom_identity_is_supported_without_manufacturer_list(self) -> None:
        custom = {
            **self.key,
            "key_id": "community-key:garage-printer",
            "subject_id": "community-device:garage-printer",
        }
        self.service.register_key(custom)
        self.assertEqual(
            custom["subject_id"],
            self.service.key(custom["key_id"])["subject_id"],
        )

    def test_key_and_attestation_schemas(self) -> None:
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError as exc:
            self.skipTest(f"optional jsonschema validator unavailable: {exc}")
        checker = FormatChecker()
        key_schema = load_json(ROOT / "schemas" / "fas" / "trust-key.schema.json")
        attestation_schema = load_json(
            ROOT / "schemas" / "fas" / "trust-attestation.schema.json"
        )
        for schema in (key_schema, attestation_schema):
            Draft202012Validator.check_schema(schema)
        Draft202012Validator(key_schema, format_checker=checker).validate(self.key)
        Draft202012Validator(attestation_schema, format_checker=checker).validate(
            self.verify()
        )


if __name__ == "__main__":
    unittest.main()
