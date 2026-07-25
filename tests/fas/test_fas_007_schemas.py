"""Validation tests for FAS-007 JSON schemas and examples."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import unittest

try:
    import jsonschema
except ImportError:  # pragma: no cover - environment-dependent test skip
    jsonschema = None


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "fas"
EXAMPLE_DIR = ROOT / "examples" / "fas"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


@unittest.skipIf(jsonschema is None, "jsonschema package is not installed")
class Fas007SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.decision_schema = load_json(
            SCHEMA_DIR / "decision-record.schema.json"
        )
        cls.evidence_schema = load_json(
            SCHEMA_DIR / "evidence-record.schema.json"
        )
        cls.decision = load_json(
            EXAMPLE_DIR / "decision-approved.example.json"
        )
        cls.evidence = load_json(
            EXAMPLE_DIR / "evidence-bed-selection.example.json"
        )

    def test_decision_example_is_valid(self) -> None:
        jsonschema.Draft202012Validator(
            self.decision_schema,
            format_checker=jsonschema.FormatChecker(),
        ).validate(self.decision)

    def test_evidence_example_is_valid(self) -> None:
        jsonschema.Draft202012Validator(
            self.evidence_schema,
            format_checker=jsonschema.FormatChecker(),
        ).validate(self.evidence)

    def test_decision_requires_evidence(self) -> None:
        invalid = deepcopy(self.decision)
        invalid["evidence_refs"] = []

        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(
                self.decision_schema
            ).validate(invalid)

    def test_confidence_cannot_exceed_one(self) -> None:
        invalid = deepcopy(self.decision)
        invalid["confidence"]["score"] = 1.01

        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(
                self.decision_schema
            ).validate(invalid)

    def test_training_eligibility_is_explicit(self) -> None:
        invalid = deepcopy(self.evidence)
        del invalid["privacy"]["training_eligible"]

        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(
                self.evidence_schema
            ).validate(invalid)

    def test_unknown_capability_identifier_is_allowed(self) -> None:
        decision = deepcopy(self.decision)
        decision["capability_refs"].append(
            {
                "id": "user-capability:custom-laser-alignment",
                "version": "user-defined-1"
            }
        )

        jsonschema.Draft202012Validator(
            self.decision_schema
        ).validate(decision)


if __name__ == "__main__":
    unittest.main()
