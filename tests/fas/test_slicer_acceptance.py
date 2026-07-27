"""Tests for non-authoritative slicer artifact acceptance."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.slicer_acceptance import (
    SlicerAcceptanceError,
    SlicerArtifactAcceptance,
)


def comparison() -> dict:
    return {
        "comparison_id": "cmp-1",
        "production": {
            "context": "production",
            "status": "succeeded",
            "artifact_digest": "d" * 64,
            "preflight_verified": True,
        },
        "twin": {
            "context": "twin",
            "status": "succeeded",
            "artifact_digest": "d" * 64,
            "preflight_verified": True,
        },
        "acceptance": {
            "status": "matching",
            "reviewed_by_user": True,
            "preflight_evidence_required": True,
        },
        "can_authorize_production": False,
    }


class SlicerAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SlicerArtifactAcceptance()

    def test_matching_reviewed_evidence_requires_final_confirmation(self) -> None:
        result = self.service.accept(comparison())
        self.assertTrue(result["ready_for_live_checks"])
        self.assertTrue(result["final_confirmation_required"])
        self.assertFalse(result["can_upload"])
        self.assertFalse(result["can_start_print"])

    def test_rejects_unreviewed_evidence(self) -> None:
        value = comparison()
        value["acceptance"]["reviewed_by_user"] = False
        with self.assertRaises(SlicerAcceptanceError):
            self.service.accept(value)

    def test_rejects_different_results(self) -> None:
        value = comparison()
        value["acceptance"]["status"] = "different"
        with self.assertRaises(SlicerAcceptanceError):
            self.service.accept(value)

    def test_rejects_raw_comparison_without_preflight(self) -> None:
        value = comparison()
        value["production"]["preflight_verified"] = False
        value["acceptance"]["preflight_evidence_required"] = False
        with self.assertRaises(SlicerAcceptanceError):
            self.service.accept(value)


if __name__ == "__main__":
    unittest.main()
