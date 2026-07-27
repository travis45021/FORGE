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
from forge.fas.twin_comparison import comparison_evidence_digest


def comparison() -> dict:
    value = {
        "comparison_id": "cmp-1",
        "input_digest": "a" * 64,
        "profile_digest": "b" * 64,
        "production": {
            "context": "production",
            "status": "succeeded",
            "artifact_digest": "d" * 64,
            "preflight_verified": True,
            "engine": {
                "name": "reviewed-engine",
                "version": "pinned",
                "source_digest": "c" * 64,
                "build_digest": "d" * 64,
            },
        },
        "twin": {
            "context": "twin",
            "status": "succeeded",
            "artifact_digest": "d" * 64,
            "preflight_verified": True,
            "engine": {
                "name": "reviewed-engine",
                "version": "pinned",
                "source_digest": "c" * 64,
                "build_digest": "d" * 64,
            },
        },
        "acceptance": {
            "status": "matching",
            "reviewed_by_user": True,
            "preflight_evidence_required": True,
            "pair_preflight_required": True,
        },
        "pair_preflight_verified": True,
        "can_authorize_production": False,
    }
    value["evidence_digest"] = comparison_evidence_digest(value)
    return value


class SlicerAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SlicerArtifactAcceptance()

    def test_matching_reviewed_evidence_requires_final_confirmation(self) -> None:
        result = self.service.accept(comparison())
        self.assertTrue(result["ready_for_live_checks"])
        self.assertTrue(result["final_confirmation_required"])
        self.assertEqual(result["input_digest"], "a" * 64)
        self.assertEqual(result["profile_digest"], "b" * 64)
        self.assertEqual(result["engine_source_digest"], "c" * 64)
        self.assertEqual(result["engine_build_digest"], "d" * 64)
        self.assertEqual(
            result["comparison_evidence_digest"],
            comparison()["evidence_digest"],
        )
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

    def test_rejects_individually_preflighted_but_unpaired_results(self) -> None:
        value = comparison()
        value["pair_preflight_verified"] = False
        value["evidence_digest"] = comparison_evidence_digest(value)
        with self.assertRaisesRegex(
            SlicerAcceptanceError, "coordinated production and twin"
        ):
            self.service.accept(value)

    def test_rejects_missing_input_or_profile_lineage(self) -> None:
        value = comparison()
        value.pop("profile_digest")
        value["evidence_digest"] = comparison_evidence_digest(value)
        with self.assertRaisesRegex(SlicerAcceptanceError, "input and profile"):
            self.service.accept(value)

    def test_rejects_missing_exact_engine_build_provenance(self) -> None:
        value = comparison()
        value["production"]["engine"].pop("build_digest")
        value["evidence_digest"] = comparison_evidence_digest(value)
        with self.assertRaisesRegex(SlicerAcceptanceError, "exact engine"):
            self.service.accept(value)

    def test_rejects_comparison_changed_after_review(self) -> None:
        value = comparison()
        value["production"]["artifact_digest"] = "e" * 64
        with self.assertRaisesRegex(SlicerAcceptanceError, "changed"):
            self.service.accept(value)


if __name__ == "__main__":
    unittest.main()
