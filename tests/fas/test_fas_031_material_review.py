import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.material_review import MaterialDesignReview, MaterialReviewError


class Fas031MaterialReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = MaterialDesignReview()

    def contract(self):
        return {
            "capability_id": "material.handling",
            "version": "1.0.0",
            "provider_id": "provider:custom-printer",
            "materials": [
                {
                    "material_id": "pla",
                    "feed_min": 0,
                    "feed_max": 1.75,
                    "max_feed_rate": 30,
                    "max_extrusion_rate": 12,
                    "retraction_supported": True,
                    "jam_behavior": "pause_and_alert",
                    "sensor_fault_behavior": "pause",
                    "temperature_reference": "thermal:hotend",
                }
            ],
            "evidence": ["evidence:material-load-001"],
        }

    def test_valid_review_is_non_authorizing(self):
        result = self.review.review(
            self.contract(),
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("accepted_for_integration_review", result["status"])
        self.assertFalse(result["execution_authorized"])

    def test_invalid_feed_limits_need_work(self):
        contract = self.contract()
        contract["materials"][0]["feed_max"] = 0
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])

    def test_wrong_capability_rejected(self):
        contract = self.contract()
        contract["capability_id"] = "thermal.management"
        with self.assertRaises(MaterialReviewError):
            self.review.review(
                contract,
                reviewer="forge-user:local",
                reviewed_at="2026-07-26T12:00:00Z",
            )

    def test_malformed_materials_and_review_metadata_fail_closed(self):
        contract = self.contract()
        contract["materials"] = {"material_id": "pla"}
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])
        with self.assertRaisesRegex(MaterialReviewError, "reviewer"):
            self.review.review(
                self.contract(), reviewer="", reviewed_at="2026-07-26T12:00:00Z"
            )
        with self.assertRaisesRegex(MaterialReviewError, "UTC"):
            self.review.review(
                self.contract(), reviewer="forge-user:local", reviewed_at="not-a-time"
            )

    def test_malformed_material_limit_types_become_findings(self):
        contract = self.contract()
        contract["materials"][0]["feed_max"] = "1.75"
        result = self.review.review(
            contract,
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("needs_work", result["status"])
        self.assertIn("limits must be numeric", result["findings"][0])


if __name__ == "__main__":
    unittest.main()
