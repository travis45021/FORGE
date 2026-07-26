import json
import unittest
from pathlib import Path

from forge.fas.health import HEALTH_STATES, HealthError, HealthService


ROOT = Path(__file__).resolve().parents[2]


def report(state="degraded"):
    return {
        "object_id": "provider:printer",
        "state": state,
        "observed_at": "2026-07-25T12:00:00Z",
        "fresh_for_seconds": 60,
        "confidence": 0.9,
        "check_type": "read_only_probe",
        "evidence": [{"kind": "response", "value": "timeout"}],
        "reason_codes": ["probe_timeout"],
        "affected_capabilities": ["printer.status"],
    }


def action(**changes):
    value = {
        "action_id": "reconnect-status",
        "scope": "provider",
        "deterministic": True,
        "physical": False,
        "risk": "low",
        "maximum_attempts": 2,
        "verification_check": "read_only_probe",
    }
    value.update(changes)
    return value


class HealthServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = HealthService()
        self.service.observe(report())

    def test_all_approved_health_states_are_supported(self):
        self.assertEqual(
            HEALTH_STATES,
            {"healthy", "unobserved", "stale", "degraded", "unavailable",
             "failed", "recovering"},
        )

    def test_observation_requires_evidence(self):
        value = report()
        value["evidence"] = []
        with self.assertRaises(HealthError):
            HealthService().observe(value)

    def test_expired_observation_becomes_stale(self):
        result = self.service.evaluate(
            "provider:printer", evaluated_at="2026-07-25T12:02:00Z"
        )
        self.assertEqual(result["state"], "stale")

    def test_diagnosis_separates_hypothesis_from_fact(self):
        result = self.service.diagnose(
            "provider:printer",
            evidence=[{"kind": "log", "ref": "event:1"}],
            hypotheses=["network unavailable"],
        )
        self.assertFalse(result["cause_confirmed"])
        self.assertEqual(result["hypotheses"][0]["status"], "unconfirmed")

    def test_dependency_impact_is_isolated(self):
        self.service.observe({**report("healthy"), "object_id": "mission:1"})
        self.service.observe({**report("healthy"), "object_id": "unrelated"})
        self.service.set_dependencies("mission:1", ["provider:printer"])
        result = self.service.impact("provider:printer")
        self.assertEqual(result["direct_dependents"], ["mission:1"])
        self.assertEqual(result["isolated_objects"], ["unrelated"])

    def test_low_risk_nonphysical_deterministic_action_is_automatic(self):
        plan = self.service.plan_recovery("provider:printer", action())
        self.assertEqual(plan["decision"], "approved_automatic")

    def test_physical_action_is_never_automatic(self):
        plan = self.service.plan_recovery(
            "provider:printer",
            action(physical=True),
            executive_authorized=True,
            safety_verified=True,
        )
        self.assertEqual(plan["decision"], "approved_manual")

    def test_physical_action_requires_authority_and_safety(self):
        plan = self.service.plan_recovery(
            "provider:printer", action(physical=True)
        )
        self.assertEqual(plan["decision"], "requires_authorization")

    def test_retry_limit_suppresses_loop(self):
        for _ in range(2):
            plan = self.service.plan_recovery("provider:printer", action())
            self.service.begin_recovery(plan)
            self.service.complete_recovery(
                "provider:printer",
                verified=False,
                evidence=[{"kind": "probe", "value": "failed"}],
            )
        plan = self.service.plan_recovery("provider:printer", action())
        self.assertEqual(plan["decision"], "suppressed")
        self.assertEqual(plan["reason"], "retry_limit_reached")

    def test_recovery_needs_verification_evidence(self):
        plan = self.service.plan_recovery("provider:printer", action())
        self.service.begin_recovery(plan)
        with self.assertRaises(HealthError):
            self.service.complete_recovery(
                "provider:printer", verified=True, evidence=[]
            )

    def test_verified_recovery_becomes_healthy(self):
        plan = self.service.plan_recovery("provider:printer", action())
        self.service.begin_recovery(plan)
        result = self.service.complete_recovery(
            "provider:printer",
            verified=True,
            evidence=[{"kind": "probe", "value": "healthy"}],
        )
        self.assertEqual(result["state"], "healthy")

    def test_schema_and_example_validate(self):
        from jsonschema import Draft202012Validator, FormatChecker

        schema = json.loads(
            (ROOT / "schemas/fas/health-report.schema.json").read_text()
        )
        example = json.loads(
            (ROOT / "examples/fas/health-report-provider.example.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).validate(example)


if __name__ == "__main__":
    unittest.main()
