import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.thermal_review import ThermalDesignReview, ThermalReviewError


class Fas030ThermalReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = ThermalDesignReview()

    def contract(self):
        return {
            "capability_id": "thermal.management",
            "version": "1.0.0",
            "provider_id": "provider:custom-printer",
            "zones": [
                {
                    "zone_id": "bed",
                    "sensor_id": "sensor:bed",
                    "minimum": 0,
                    "maximum": 120,
                    "control_mode": "pid",
                    "max_rate": 3,
                    "overtemperature_behavior": "cut_power",
                    "sensor_fault_behavior": "cut_power_and_pause",
                    "power_interlock": "hardware_relay",
                }
            ],
            "evidence": ["evidence:thermal-calibration-001"],
        }

    def test_valid_review_is_non_authorizing(self):
        result = self.review.review(
            self.contract(),
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("accepted_for_integration_review", result["status"])
        self.assertFalse(result["execution_authorized"])

    def test_invalid_zone_is_needs_work(self):
        contract = self.contract()
        contract["zones"][0]["maximum"] = 0
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])

    def test_wrong_capability_rejected(self):
        contract = self.contract()
        contract["capability_id"] = "motion.positioning"
        with self.assertRaises(ThermalReviewError):
            self.review.review(
                contract,
                reviewer="forge-user:local",
                reviewed_at="2026-07-26T12:00:00Z",
            )

    def test_malformed_zones_and_review_metadata_fail_closed(self):
        contract = self.contract()
        contract["zones"] = {"zone_id": "bed"}
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])
        with self.assertRaisesRegex(ThermalReviewError, "reviewer"):
            self.review.review(
                self.contract(), reviewer="", reviewed_at="2026-07-26T12:00:00Z"
            )
        with self.assertRaisesRegex(ThermalReviewError, "UTC"):
            self.review.review(
                self.contract(), reviewer="forge-user:local", reviewed_at="not-a-time"
            )

    def test_malformed_zone_limit_types_become_findings(self):
        contract = self.contract()
        contract["zones"][0]["maximum"] = "120"
        result = self.review.review(
            contract,
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("needs_work", result["status"])
        self.assertIn("limits must be numeric", result["findings"][0])


if __name__ == "__main__":
    unittest.main()
