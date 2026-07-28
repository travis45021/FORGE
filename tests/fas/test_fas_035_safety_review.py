import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.safety_review import SafetyDesignReview, SafetyReviewError


class Fas035SafetyReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = SafetyDesignReview()

    def contract(self):
        return {
            "capability_id": "environment.safety",
            "version": "1.0.0",
            "provider_id": "provider:safety",
            "sensors": [
                {
                    "sensor_id": "safety:door",
                    "kind": "interlock",
                    "normal_range": "closed",
                    "trip_behavior": "stop_and_power_cut",
                    "loss_behavior": "stop_and_alert",
                    "independent_path": True,
                }
            ],
            "evidence": ["evidence:safety-test-001"],
        }

    def test_valid_review_is_non_authorizing(self):
        result = self.review.review(
            self.contract(),
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertFalse(result["execution_authorized"])

    def test_missing_independent_path_needs_work(self):
        contract = self.contract()
        contract["sensors"][0]["independent_path"] = False
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])

    def test_wrong_capability_rejected(self):
        contract = self.contract()
        contract["capability_id"] = "thermal.management"
        with self.assertRaises(SafetyReviewError):
            self.review.review(
                contract,
                reviewer="forge-user:local",
                reviewed_at="2026-07-26T12:00:00Z",
            )

    def test_malformed_sensors_and_review_metadata_fail_closed(self):
        contract = self.contract()
        contract["sensors"] = {"sensor_id": "safety:door"}
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])
        with self.assertRaisesRegex(SafetyReviewError, "reviewer"):
            self.review.review(
                self.contract(), reviewer="", reviewed_at="2026-07-26T12:00:00Z"
            )
        with self.assertRaisesRegex(SafetyReviewError, "UTC"):
            self.review.review(
                self.contract(), reviewer="forge-user:local", reviewed_at="not-a-time"
            )

    def test_malformed_safety_behavior_becomes_findings(self):
        contract = self.contract()
        contract["sensors"][0]["trip_behavior"] = 42
        result = self.review.review(
            contract,
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("needs_work", result["status"])
        self.assertTrue(
            any(
                "trip_behavior is required" in finding for finding in result["findings"]
            )
        )


if __name__ == "__main__":
    unittest.main()
