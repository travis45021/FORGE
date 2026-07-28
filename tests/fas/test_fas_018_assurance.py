"""Behavior and schema tests for canonical FAS-018."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.assurance import (
    CLASS_CHECKS,
    AssuranceError,
    AssuranceService,
    context_fingerprint,
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas018AssuranceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = load_json(
            ROOT / "examples" / "fas" / "verification-packet-calibration.example.json"
        )
        self.context = {
            "printer_id": "community-device:garage-printer",
            "nozzle_mm": 0.4,
            "material_profile": "forge-material:petg-black",
        }
        self.service = AssuranceService()

    def evaluate(self, packet: dict | None = None, **changes: object) -> dict:
        return self.service.evaluate(
            packet or self.packet,
            current_context=self.context,
            evaluated_at="2026-07-25T21:00:00Z",
            **changes,
        )

    def test_verified_recommendation_preserves_uncertainty(self) -> None:
        result = self.evaluate()
        self.assertEqual("verified", result["disposition"])
        self.assertEqual("verified_recommendation", result["claim_state"])
        self.assertTrue(result["uncertainties"])

    def test_context_change_and_expiry_block_reuse(self) -> None:
        changed = {**self.context, "nozzle_mm": 0.6}
        result = self.service.evaluate(
            self.packet,
            current_context=changed,
            evaluated_at="2026-07-25T21:00:00Z",
        )
        self.assertEqual("context_changed", result["reason_code"])
        expired = deepcopy(self.packet)
        expired["expires_at"] = "2026-07-25T20:00:00Z"
        self.assertEqual("verification_expired", self.evaluate(expired)["reason_code"])

    def test_failed_and_incomplete_checks_fail_closed(self) -> None:
        failed = deepcopy(self.packet)
        failed["failed_checks"] = ["compatibility"]
        failed["completed_checks"].remove("compatibility")
        self.assertEqual("required_check_failed", self.evaluate(failed)["reason_code"])
        incomplete = deepcopy(self.packet)
        incomplete["completed_checks"].remove("compatibility")
        self.assertEqual("checks_incomplete", self.evaluate(incomplete)["reason_code"])

    def test_assurance_class_minimum_checks_are_enforced(self) -> None:
        changed = deepcopy(self.packet)
        changed["required_checks"].remove("recovery")
        changed["completed_checks"].remove("recovery")
        with self.assertRaisesRegex(AssuranceError, "missing required checks"):
            self.evaluate(changed)

    def test_authorization_is_separate_from_verification(self) -> None:
        packet = deepcopy(self.packet)
        packet["assurance_class"] = "A3"
        packet["claim_state"] = "authorized_action"
        packet["required_checks"] = sorted(CLASS_CHECKS["A3"])
        packet["completed_checks"] = sorted(CLASS_CHECKS["A3"])
        result = self.evaluate(packet)
        self.assertEqual("verified_recommendation", result["claim_state"])
        self.assertEqual("authority_not_verified", result["reason_code"])
        result = self.evaluate(packet, authorization_verified=True)
        self.assertEqual("authorized_action", result["claim_state"])

    def test_a5_is_explicitly_future_gated(self) -> None:
        changed = {**self.packet, "assurance_class": "A5"}
        with self.assertRaisesRegex(AssuranceError, "future-gated"):
            self.evaluate(changed)

    def test_safety_critical_checks_cannot_be_waived(self) -> None:
        packet = deepcopy(self.packet)
        packet["assurance_class"] = "A4"
        packet["claim_state"] = "authorized_action"
        packet["required_checks"] = sorted(CLASS_CHECKS["A4"])
        packet["completed_checks"] = sorted(CLASS_CHECKS["A4"] - {"safety"})
        packet["waived_checks"] = ["safety"]
        packet["waiver"] = {"authorized_by": "forge-user:admin"}
        with self.assertRaisesRegex(AssuranceError, "cannot be waived"):
            self.evaluate(packet, authorization_verified=True)

    def test_measured_outcome_requires_verified_packet_and_evidence(self) -> None:
        self.evaluate()
        outcome = self.service.record_outcome(
            self.packet["verification_id"],
            measured_at="2026-07-25T22:00:00Z",
            success=False,
            measurements={"corner_error_mm": 0.3},
            evidence_refs=["forge-evidence:outcome-001"],
        )
        self.assertEqual("measured_outcome", outcome["claim_state"])
        self.assertTrue(outcome["requires_revalidation"])

    def test_context_fingerprint_is_deterministic(self) -> None:
        reordered = dict(reversed(list(self.context.items())))
        self.assertEqual(
            context_fingerprint(self.context), context_fingerprint(reordered)
        )

    def test_malformed_check_entries_fail_as_assurance_errors(self) -> None:
        packet = deepcopy(self.packet)
        packet["completed_checks"] = [{"check": "source"}]
        with self.assertRaisesRegex(AssuranceError, "unique list"):
            self.evaluate(packet)

    def test_schema_and_example_validate(self) -> None:
        from jsonschema import Draft202012Validator, FormatChecker

        schema = load_json(ROOT / "schemas" / "fas" / "verification-packet.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(
            self.packet
        )


if __name__ == "__main__":
    unittest.main()
