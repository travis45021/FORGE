import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.design_review import DesignReviewError, MotionDesignReview


class Fas029DesignReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = MotionDesignReview()

    def contract(self):
        return {
            "capability_id": "motion.positioning",
            "version": "1.0.0",
            "provider_id": "provider:custom-printer",
            "axes": [
                {
                    "axis_id": "x",
                    "unit": "mm",
                    "minimum": 0,
                    "maximum": 300,
                    "max_velocity": 300,
                    "max_acceleration": 5000,
                    "homing_required": True,
                    "limit_behavior": "stop",
                    "fault_behavior": "pause",
                }
            ],
            "evidence": ["evidence:motion-calibration-001"],
        }

    def test_valid_review_never_authorizes_execution(self):
        result = self.review.review(
            self.contract(),
            reviewer="forge-user:local",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("accepted_for_integration_review", result["status"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["hardware_safety_asserted"])

    def test_invalid_limits_are_findings(self):
        contract = self.contract()
        contract["axes"][0]["maximum"] = 0
        result = self.review.review(
            contract, reviewer="forge-user:local", reviewed_at="2026-07-26T12:00:00Z"
        )
        self.assertEqual("needs_work", result["status"])
        self.assertTrue(result["findings"])

    def test_wrong_capability_is_rejected(self):
        contract = self.contract()
        contract["capability_id"] = "thermal"
        with self.assertRaises(DesignReviewError):
            self.review.review(
                contract,
                reviewer="forge-user:local",
                reviewed_at="2026-07-26T12:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
