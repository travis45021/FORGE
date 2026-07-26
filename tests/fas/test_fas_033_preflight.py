import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.preflight import ArtifactPreflight, PreflightError


class Fas033PreflightTests(unittest.TestCase):
    def setUp(self):
        self.service = ArtifactPreflight()

    def artifact(self, fmt="3mf"):
        return {
            "artifact_id": "artifact:001",
            "filename": "part.3mf",
            "format": fmt,
            "digest": "sha256:" + "a" * 64,
            "size_bytes": 1200,
        }

    def test_step_and_3mf_are_accepted_for_validation(self):
        result = self.service.validate(
            self.artifact(), checks={"structure": True, "units": True}
        )
        self.assertEqual("passed", result["validation_status"])
        self.assertTrue(result["requires_user_review"])
        self.assertFalse(result["print_authorized"])

    def test_gcode_is_inspectable_but_not_authority(self):
        result = self.service.inspect(self.artifact("gcode"))
        self.assertEqual("needs_review", result["status"])
        self.assertFalse(result["slicing_authorized"])

    def test_f3d_is_deferred_and_failed_checks_are_recorded(self):
        result = self.service.validate(
            self.artifact("f3d"), checks={"structure": False}
        )
        self.assertEqual("failed", result["validation_status"])
        self.assertTrue(any("deferred" in finding for finding in result["findings"]))

    def test_missing_identity_rejected(self):
        with self.assertRaises(PreflightError):
            self.service.inspect({"format": "stl"})


if __name__ == "__main__":
    unittest.main()
