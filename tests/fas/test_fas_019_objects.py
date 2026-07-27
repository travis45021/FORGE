"""Behavior and schema tests for canonical FAS-019."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.objects import ObjectSystem, ObjectSystemError


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas019ObjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.extruder = load_json(
            ROOT / "examples" / "fas" / "forge-object-custom-extruder.example.json"
        )
        self.system = ObjectSystem()

    def object_variant(self, object_id: str, object_type: str, name: str) -> dict:
        item = deepcopy(self.extruder)
        item.update(
            {"object_id": object_id, "object_type": object_type, "display_name": name}
        )
        return item

    def test_custom_identity_remains_honest_and_provisional(self) -> None:
        result = self.system.create(self.extruder)
        self.assertEqual("Custom Extruder", result["display_name"])
        self.assertIsNone(result["metadata"]["manufacturer"])
        self.assertEqual("provisional", result["lifecycle_state"])
        self.assertTrue(result["unknown_fields"])

    def test_identity_is_immutable_and_display_name_is_editable(self) -> None:
        self.system.create(self.extruder)
        with self.assertRaisesRegex(ObjectSystemError, "immutable"):
            self.system.create(self.extruder)
        changed = self.system.update(
            self.extruder["object_id"],
            {"display_name": "Garage Extruder"},
            updated_at="2026-07-25T21:00:00Z",
            reason="user renamed component",
            evidence_refs=["forge-evidence:user-change-001"],
        )
        self.assertEqual(self.extruder["object_id"], changed["object_id"])
        self.assertEqual(2, changed["version"])

    def test_state_health_limits_and_policy_remain_separate(self) -> None:
        item = self.system.create(self.extruder)
        self.assertIn("operating_state", item["state"])
        self.assertIn("state", item["health"])
        self.assertIn("maximum_temperature_c", item["limits"])
        self.assertIsInstance(item["policies"], list)

    def test_typed_relationship_requires_objects_and_evidence(self) -> None:
        printer = self.object_variant(
            "forge-object:printer-001", "hardware.printer", "Custom Printer"
        )
        self.system.create(printer)
        self.system.create(self.extruder)
        relation = self.system.add_relationship(
            {
                "relationship_id": "forge-relationship:printer-extruder",
                "source_id": printer["object_id"],
                "relationship_type": "contains",
                "target_id": self.extruder["object_id"],
                "scope": "installation:local",
                "knowledge_state": "user_declared",
                "evidence_refs": ["forge-evidence:assembly-001"],
                "created_at": "2026-07-25T21:00:00Z",
                "active": True,
                "reason": "user confirmed assembly",
            }
        )
        self.assertEqual("contains", relation["relationship_type"])
        self.assertEqual(1, len(self.system.neighbors(printer["object_id"])))

    def test_update_history_preserves_prior_version(self) -> None:
        self.system.create(self.extruder)
        self.system.update(
            self.extruder["object_id"],
            {"limits": {"maximum_temperature_c": 295}},
            updated_at="2026-07-25T21:00:00Z",
            reason="locally measured safe limit",
            evidence_refs=["forge-evidence:limit-test-001"],
        )
        versions = self.system.versions(self.extruder["object_id"])
        self.assertEqual(285, versions[0]["limits"]["maximum_temperature_c"])
        self.assertEqual(295, versions[1]["limits"]["maximum_temperature_c"])

    def test_operational_twin_is_opt_in_and_not_simulation(self) -> None:
        self.system.create(self.extruder)
        with self.assertRaisesRegex(ObjectSystemError, "user choice"):
            self.system.operational_twin(self.extruder["object_id"], user_enabled=False)
        twin = self.system.operational_twin(
            self.extruder["object_id"],
            user_enabled=True,
            active_mission={"mission_id": "forge-mission:calibration"},
        )
        self.assertFalse(twin["simulation"])
        self.assertFalse(twin["authoritative"])
        self.assertEqual("operational", twin["scope"])

    def test_degradation_affects_only_dependencies(self) -> None:
        degraded = deepcopy(self.extruder)
        degraded["health"]["state"] = "degraded"
        self.system.create(degraded)
        impact = self.system.affected_by_health(degraded["object_id"])
        self.assertEqual(["material.extrusion"], impact["affected_capabilities"])
        self.assertTrue(impact["unrelated_objects_remain_available"])

    def test_object_requires_provenance_and_explicit_unknowns(self) -> None:
        changed = {**self.extruder, "evidence_refs": []}
        with self.assertRaisesRegex(ObjectSystemError, "provenance"):
            self.system.create(changed)
        changed = {**self.extruder, "unknown_fields": None}
        with self.assertRaisesRegex(ObjectSystemError, "must be a list"):
            self.system.create(changed)

    def test_no_hardware_or_simulation_authority_surface(self) -> None:
        self.assertFalse(hasattr(self.system, "command_hardware"))
        self.assertFalse(hasattr(self.system, "authorize"))
        self.assertFalse(hasattr(self.system, "simulate_physics"))

    def test_schema_and_example_validate(self) -> None:
        from jsonschema import Draft202012Validator, FormatChecker

        schema = load_json(ROOT / "schemas" / "fas" / "forge-object.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(
            self.extruder
        )


if __name__ == "__main__":
    unittest.main()
