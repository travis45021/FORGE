import json
import unittest
from pathlib import Path

from forge.fas.testing import TEST_LAYERS, TestAssuranceError, TestAssuranceService

ROOT = Path(__file__).resolve().parents[2]


def result(**changes):
    value = {
        "test_id": "scenario-1",
        "layer": "scenario",
        "test_version": "1.0",
        "contract_versions": {"provider": "v1"},
        "configuration_snapshot": {"profile": "default"},
        "provider_versions": {"printer": "sim-1"},
        "input_data": {"mission": "demo"},
        "event_sequence": ["mission.started", "mission.completed"],
        "runtime_context": {"simulated": True},
        "expected": "completed",
        "observed": "completed",
        "outcome": "passed",
        "random_seed": 42,
    }
    value.update(changes)
    return value


class TestAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.service = TestAssuranceService()

    def test_all_layers_are_distinct(self):
        self.assertEqual(len(TEST_LAYERS), 8)
        self.assertIn("hardware_in_the_loop", TEST_LAYERS)

    def test_simulator_is_honestly_nonproduction(self):
        registered = self.service.register_simulator(
            {
                "provider_id": "sim:printer",
                "represented_behavior": "printer status",
                "contract_version": "v1",
                "limitations": ["no physical timing"],
                "failure_modes": ["disconnect"],
                "deterministic": True,
                "suitable_layers": ["scenario", "fault_injection"],
            }
        )
        self.assertFalse(registered["production_eligible"])
        self.assertFalse(registered["can_authorize_physical_action"])

    def test_production_context_never_allows_simulation(self):
        context = self.service.execution_context(context_kind="production")
        self.assertFalse(context["simulation_allowed"])
        self.assertFalse(context["physical_authority_from_simulation"])

    def test_reproducibility_fields_are_required(self):
        value = result()
        del value["event_sequence"]
        with self.assertRaises(TestAssuranceError):
            self.service.record_result(value)

    def test_variable_test_needs_acceptance_range(self):
        with self.assertRaises(TestAssuranceError):
            self.service.record_result(result(variable=True))

    def test_simulation_is_evidence_not_authority(self):
        recorded = self.service.record_result(result())
        self.assertEqual(recorded["evidence_kind"], "simulation")
        self.assertFalse(recorded["authorizes_production"])

    def test_hardware_test_requires_authority_and_bounds(self):
        plan = {
            "target_hardware": "printer:1",
            "limits": {"distance_mm": 1},
            "stop_conditions": ["unexpected_motion"],
            "physical_action": "move_axis",
            "monitoring": ["position"],
            "recovery_plan": "emergency_stop",
            "mission_kind": "test",
        }
        with self.assertRaises(TestAssuranceError):
            self.service.validate_hardware_test(plan, user_authorized=False)
        accepted = self.service.validate_hardware_test(plan, user_authorized=True)
        self.assertTrue(accepted["bounded"])

    def test_failed_required_test_blocks_release(self):
        record = self._release()
        record["test_results"][0]["outcome"] = "failed"
        assessed = self.service.assess_release(record)
        self.assertEqual(assessed["decision"], "blocked")

    def test_security_regression_blocks_release(self):
        record = self._release()
        record["security_review"] = "failed"
        assessed = self.service.assess_release(record)
        self.assertEqual(assessed["decision"], "blocked")

    def test_incomplete_compatibility_review_blocks_release(self):
        record = self._release()
        record["compatibility_review"] = "incomplete"
        assessed = self.service.assess_release(record)
        self.assertEqual(assessed["decision"], "blocked")
        self.assertIn(
            {"reason": "compatibility_review_not_passed"},
            assessed["blocking_evidence"],
        )

    def test_complete_release_record_is_ready_for_release_gate_only(self):
        assessed = self.service.assess_release(self._release())
        self.assertEqual(assessed["decision"], "ready_for_release_gate")
        self.assertEqual(assessed["maturity_claim"], "bounded_by_recorded_evidence")
        self.assertFalse(assessed["release_authorized"])
        self.assertFalse(assessed["physical_execution_authorized"])

    def test_placeholder_integrity_digest_is_rejected(self):
        record = self._release()
        record["integrity"]["digest"] = "record-at-package-time"
        with self.assertRaisesRegex(TestAssuranceError, "SHA-256"):
            self.service.assess_release(record)

    def test_unknown_release_fields_are_rejected(self):
        record = self._release()
        record["publish_now"] = True
        with self.assertRaisesRegex(TestAssuranceError, "unknown release"):
            self.service.assess_release(record)

    def test_schema_and_example_validate(self):
        from jsonschema import Draft202012Validator

        schema = json.loads(
            (ROOT / "schemas/fas/release-assurance.schema.json").read_text()
        )
        example = json.loads(
            (ROOT / "examples/fas/release-assurance.example.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(example)

    @staticmethod
    def _release():
        return {
            "release_version": "0.25.0",
            "components": ["forge-core"],
            "supported_environments": ["local-python-3.10"],
            "test_results": [{"suite": "core", "outcome": "passed", "required": True}],
            "known_limitations": ["no cloud interface"],
            "security_review": "passed",
            "compatibility_review": "passed",
            "migration": "none",
            "rollback": "restore previous package",
            "documentation_complete": True,
            "integrity": {"algorithm": "sha256", "digest": "a" * 64},
        }


if __name__ == "__main__":
    unittest.main()
