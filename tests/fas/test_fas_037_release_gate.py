import sys
import unittest
from copy import deepcopy
from json import loads
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.release_gate import REQUIRED_GATES, ReleaseGate, ReleaseGateError


class Fas037ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = ReleaseGate()
        self.evidence = {name: True for name in REQUIRED_GATES}

    def test_complete_evidence_is_ready_for_human_decision_only(self):
        result = self.gate.evaluate(
            self.evidence,
            reviewed_by="forge-user:release",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("ready_for_final_human_decision", result["status"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(self.evidence, result["evidence"])
        self.assertRegex(result["evidence_digest"], r"^sha256:[0-9a-f]{64}$")

    def test_failed_gate_blocks_release(self):
        self.evidence["licensing"] = False
        result = self.gate.evaluate(
            self.evidence,
            reviewed_by="forge-user:release",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual(["licensing"], result["failed_gates"])

    def test_missing_gate_rejected(self):
        self.evidence.pop("security")
        with self.assertRaises(ReleaseGateError):
            self.gate.evaluate(
                self.evidence,
                reviewed_by="forge-user:release",
                reviewed_at="2026-07-26T12:00:00Z",
            )

    def test_unknown_gate_rejected(self):
        self.evidence["automatic_publication"] = True
        with self.assertRaisesRegex(ReleaseGateError, "unknown release evidence"):
            self.gate.evaluate(
                self.evidence,
                reviewed_by="forge-user:release",
                reviewed_at="2026-07-26T12:00:00Z",
            )

    def test_non_boolean_gate_rejected(self):
        self.evidence["licensing"] = 1
        with self.assertRaisesRegex(ReleaseGateError, "explicit booleans"):
            self.gate.evaluate(
                self.evidence,
                reviewed_by="forge-user:release",
                reviewed_at="2026-07-26T12:00:00Z",
            )

    def test_invalid_review_timestamp_rejected(self):
        with self.assertRaisesRegex(ReleaseGateError, "UTC"):
            self.gate.evaluate(
                self.evidence,
                reviewed_by="forge-user:release",
                reviewed_at="2026-07-26T12:00:00",
            )

    def test_automation_reviewer_labels_are_rejected(self):
        for reviewer in ("automation", "forge-review:ci", "system"):
            with (
                self.subTest(reviewer=reviewer),
                self.assertRaisesRegex(ReleaseGateError, "human reviewer"),
            ):
                self.gate.evaluate(
                    self.evidence,
                    reviewed_by=reviewer,
                    reviewed_at="2026-07-26T12:00:00Z",
                )

    def test_evidence_digest_is_deterministic(self):
        reversed_evidence = dict(reversed(list(self.evidence.items())))
        first = self.gate.evaluate(
            self.evidence,
            reviewed_by="forge-user:release",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        second = self.gate.evaluate(
            reversed_evidence,
            reviewed_by="forge-user:release",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual(first["evidence_digest"], second["evidence_digest"])

    def test_output_and_published_example_match_strict_schema(self):
        schema = loads(
            (ROOT / "schemas/fas/v1-release-gate.schema.json").read_text(
                encoding="utf-8"
            )
        )
        example = loads(
            (ROOT / "examples/fas/v1-release-gate.example.json").read_text(
                encoding="utf-8"
            )
        )
        generated = self.gate.evaluate(
            self.evidence,
            reviewed_by="forge-user:release",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        jsonschema.Draft202012Validator(schema).validate(generated)
        jsonschema.Draft202012Validator(schema).validate(example)
        regenerated_example = self.gate.evaluate(
            example["evidence"],
            reviewed_by=example["reviewed_by"],
            reviewed_at=example["reviewed_at"],
        )
        self.assertEqual(
            example["evidence_digest"], regenerated_example["evidence_digest"]
        )
        self.assertEqual(example["status"], regenerated_example["status"])
        self.assertEqual(example["failed_gates"], regenerated_example["failed_gates"])

        mutated = deepcopy(example)
        mutated["release_authorized"] = True
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(mutated)


if __name__ == "__main__":
    unittest.main()
