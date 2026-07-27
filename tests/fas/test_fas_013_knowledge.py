"""Behavior and schema tests for canonical FAS-013."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.knowledge import KnowledgeCore, KnowledgeError


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas013KnowledgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = load_json(
            ROOT / "examples" / "fas" / "knowledge-nozzle.example.json"
        )
        self.core = KnowledgeCore()

    def test_local_fact_and_explanation(self) -> None:
        self.core.create(self.item)
        explanation = self.core.explain(self.item["knowledge_id"])
        self.assertEqual(0.4, explanation["claim"]["value"])
        self.assertEqual("user_confirmation", explanation["source_class"])

    def test_provenance_is_required(self) -> None:
        changed = {**self.item, "source_refs": []}
        with self.assertRaisesRegex(KnowledgeError, "provenance"):
            self.core.create(changed)

    def test_shared_knowledge_is_advisory_until_adopted(self) -> None:
        shared = {**self.item, "knowledge_id": "community-knowledge:nozzle"}
        shared.update({"origin": "shared", "status": "advisory"})
        self.core.create(shared)
        adopted = self.core.adopt_shared(
            shared["knowledge_id"],
            adopted_by="forge-user:owner",
            adopted_at="2026-07-25T21:00:00Z",
        )
        self.assertEqual("local", adopted["origin"])
        self.assertEqual("provisional", adopted["status"])

    def test_shared_active_truth_is_rejected(self) -> None:
        changed = {**self.item, "origin": "shared"}
        with self.assertRaisesRegex(KnowledgeError, "advisory"):
            self.core.create(changed)

    def test_ai_cannot_create_authoritative_fact(self) -> None:
        changed = {**self.item, "source_class": "ai"}
        with self.assertRaisesRegex(KnowledgeError, "provisional"):
            self.core.create(changed)
        changed.update(
            {
                "knowledge_type": "inference",
                "status": "provisional",
                "requires_verification": True,
            }
        )
        self.core.create(changed)

    def test_user_correction_preserves_supersession(self) -> None:
        self.core.create(self.item)
        corrected = self.core.correct(
            self.item["knowledge_id"],
            corrected_id="forge-knowledge:nozzle-primary-060",
            value=0.6,
            corrected_by="forge-user:owner",
            corrected_at="2026-07-25T21:00:00Z",
            reason="user changed nozzle",
        )
        self.assertEqual(0.6, corrected["value"])
        prior = self.core.item(self.item["knowledge_id"])
        self.assertEqual("superseded", prior["status"])
        self.assertEqual(corrected["knowledge_id"], prior["superseded_by"])

    def test_dependency_change_marks_related_knowledge_stale(self) -> None:
        self.core.create(self.item)
        dependent = deepcopy(self.item)
        dependent.update(
            {
                "knowledge_id": "forge-knowledge:pressure-advance",
                "predicate": "pressure_advance",
                "value": 0.04,
                "depends_on": [self.item["knowledge_id"]],
            }
        )
        self.core.create(dependent)
        self.core.correct(
            self.item["knowledge_id"],
            corrected_id="forge-knowledge:nozzle-primary-060",
            value=0.6,
            corrected_by="forge-user:owner",
            corrected_at="2026-07-25T21:00:00Z",
            reason="user changed nozzle",
        )
        self.assertEqual("stale", self.core.item(dependent["knowledge_id"])["status"])

    def test_export_is_complete_and_deterministic(self) -> None:
        self.core.create(self.item)
        first = self.core.export()
        second = self.core.export()
        self.assertEqual(first, second)
        self.assertEqual(1, len(first["items"]))
        self.assertEqual(1, len(first["history"]))

    def test_schema_and_example_validate(self) -> None:
        from jsonschema import Draft202012Validator, FormatChecker

        schema = load_json(ROOT / "schemas" / "fas" / "knowledge-object.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(self.item)


if __name__ == "__main__":
    unittest.main()
