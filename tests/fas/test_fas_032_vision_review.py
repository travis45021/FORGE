import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.vision_review import VisionDesignReview, VisionReviewError


class Fas032VisionReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = VisionDesignReview()

    def contract(self):
        return {
            "capability_id": "vision.observation",
            "version": "1.0.0",
            "provider_id": "provider:camera",
            "sensors": [
                {
                    "sensor_id": "camera:1",
                    "modality": "rgb",
                    "resolution": "1920x1080",
                    "rate": 30,
                    "privacy_mode": "local_only",
                    "failure_behavior": "mark_unavailable",
                }
            ],
            "evidence": ["evidence:camera-check-001"],
        }

    def test_valid_review_is_optional_and_non_authorizing(self):
        result = self.review.review(
            self.contract(),
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertFalse(result["v1_required"])
        self.assertFalse(result["execution_authorized"])

    def test_invalid_privacy_mode_needs_work(self):
        contract = self.contract()
        contract["sensors"][0]["privacy_mode"] = "cloud_upload"
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])

    def test_wrong_capability_rejected(self):
        contract = self.contract()
        contract["capability_id"] = "thermal.management"
        with self.assertRaises(VisionReviewError):
            self.review.review(
                contract,
                reviewer="forge-user:local",
                reviewed_at="2026-07-26T12:00:00Z",
            )

    def test_malformed_sensors_and_review_metadata_fail_closed(self):
        contract = self.contract()
        contract["sensors"] = {"sensor_id": "camera:1"}
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])
        with self.assertRaisesRegex(VisionReviewError, "reviewer"):
            self.review.review(
                self.contract(), reviewer="", reviewed_at="2026-07-26T12:00:00Z"
            )
        with self.assertRaisesRegex(VisionReviewError, "UTC"):
            self.review.review(
                self.contract(), reviewer="forge-user:local", reviewed_at="not-a-time"
            )

    def test_malformed_sensor_rate_types_become_findings(self):
        contract = self.contract()
        contract["sensors"][0]["rate"] = "30"
        result = self.review.review(
            contract,
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("needs_work", result["status"])
        self.assertIn("rate must be numeric", result["findings"][0])


if __name__ == "__main__":
    unittest.main()
