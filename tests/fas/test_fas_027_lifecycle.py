import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.lifecycle import LifecycleError, ServiceLifecycle


class Fas027LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.service = ServiceLifecycle()
        self.manifest = {
            "service_id": "forge-service:local-api",
            "version": "1.0.0",
            "dependencies": [],
            "provides": ["local-api"],
            "state": "registered",
        }
        self.service.register(self.manifest)

    def test_explicit_start_plan_has_no_physical_authority(self):
        plan = self.service.plan_start(
            self.manifest["service_id"],
            requested_by="forge-user:local",
            approval_reference="decision:1",
        )
        self.assertFalse(plan["physical_commands_allowed"])

    def test_transition_requires_authority_and_dependency_health(self):
        with self.assertRaises(LifecycleError):
            self.service.transition(
                self.manifest["service_id"],
                "starting",
                reason="boot",
                authority_reference="",
                observed_at="2026-07-26T12:00:00Z",
            )
        self.service.transition(
            self.manifest["service_id"],
            "starting",
            reason="boot",
            authority_reference="decision:1",
            observed_at="2026-07-26T12:00:00Z",
        )
        ready = self.service.transition(
            self.manifest["service_id"],
            "ready",
            reason="healthy",
            authority_reference="decision:1",
            observed_at="2026-07-26T12:00:01Z",
            health="healthy",
        )
        self.assertEqual("ready", ready["state"])

    def test_invalid_transition_and_stop_requires_request(self):
        with self.assertRaises(LifecycleError):
            self.service.transition(
                self.manifest["service_id"],
                "ready",
                reason="skip",
                authority_reference="decision:1",
                observed_at="2026-07-26T12:00:00Z",
            )
        with self.assertRaises(LifecycleError):
            self.service.plan_stop(
                self.manifest["service_id"],
                requested_by="",
                approval_reference="decision:1",
            )

    def test_transition_rejects_non_utc_observation(self):
        with self.assertRaisesRegex(LifecycleError, "UTC"):
            self.service.transition(
                self.manifest["service_id"],
                "starting",
                reason="boot",
                authority_reference="decision:1",
                observed_at="2026-07-26T12:00:00-05:00",
            )

    def test_manifest_rejects_duplicate_or_self_dependencies(self):
        duplicate = dict(self.manifest)
        duplicate["dependencies"] = ["forge-service:worker", "forge-service:worker"]
        with self.assertRaisesRegex(LifecycleError, "duplicates"):
            ServiceLifecycle().register(duplicate)
        self_reference = dict(self.manifest)
        self_reference["dependencies"] = [self.manifest["service_id"]]
        with self.assertRaisesRegex(LifecycleError, "itself"):
            ServiceLifecycle().register(self_reference)

    def test_recovery_plan_is_review_gated_and_fails_closed(self):
        self.service.transition(
            self.manifest["service_id"],
            "starting",
            reason="boot",
            authority_reference="decision:1",
            observed_at="2026-07-26T12:00:00Z",
        )
        self.service.transition(
            self.manifest["service_id"],
            "failed",
            reason="crash",
            authority_reference="decision:1",
            observed_at="2026-07-26T12:00:01Z",
            health="failed",
        )
        plan = self.service.plan_recovery(
            self.manifest["service_id"],
            requested_by="forge-user:local",
            approval_reference="decision:recovery-1",
            reason="user requested crash recovery review",
        )
        self.assertTrue(plan["requires_fresh_context"])
        self.assertFalse(plan["automatic_restart_allowed"])
        self.assertFalse(plan["physical_commands_allowed"])
        with self.assertRaisesRegex(LifecycleError, "requester"):
            self.service.plan_recovery(
                self.manifest["service_id"],
                requested_by="",
                approval_reference="decision:recovery-1",
                reason="review",
            )


if __name__ == "__main__":
    unittest.main()
