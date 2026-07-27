"""Behavior tests for production/twin comparison evidence."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.twin_comparison import TwinComparisonError, TwinComparisonService


def result(context: str, artifact: str = "d") -> dict:
    return {
        "request_id": f"req-{context}",
        "status": "succeeded",
        "context": context,
        "engine": {"name": "engine", "version": "1", "source_digest": "c" * 64},
        "artifact_digest": artifact * 64,
        "warnings": [],
        "authority": {"can_upload": False, "can_start_print": False},
    }


class TwinComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TwinComparisonService()

    def test_matching_results_remain_non_authoritative(self) -> None:
        comparison = self.service.compare(
            comparison_id="cmp-1",
            input_digest="a" * 64,
            production=result("production"),
            twin=result("twin"),
        )
        self.assertEqual(comparison["acceptance"]["status"], "matching")
        self.assertFalse(comparison["can_authorize_production"])

    def test_reports_artifact_difference(self) -> None:
        comparison = self.service.compare(
            comparison_id="cmp-1",
            input_digest="a" * 64,
            production=result("production", "d"),
            twin=result("twin", "e"),
        )
        self.assertIn("artifact_digest", comparison["differences"])

    def test_rejects_context_swap(self) -> None:
        with self.assertRaises(TwinComparisonError):
            self.service.compare(
                comparison_id="cmp-1",
                input_digest="a" * 64,
                production=result("twin"),
                twin=result("production"),
            )


if __name__ == "__main__":
    unittest.main()
