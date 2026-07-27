"""Tests for provider-neutral live printer evidence."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.live_printer_checks import (
    REQUIRED_CHECKS,
    LivePrinterCheckError,
    LivePrinterCheckService,
)


class LivePrinterCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = LivePrinterCheckService()
        self.checks = {name: True for name in REQUIRED_CHECKS}

    def evaluate(self) -> dict:
        return self.service.evaluate(
            provider_id="provider:custom-printer",
            artifact_digest="a" * 64,
            checks=self.checks,
            checked_at="2026-07-26T12:04:00Z",
            expires_at="2026-07-26T12:09:00Z",
        )

    def test_pass_still_requires_final_confirmation(self) -> None:
        result = self.evaluate()
        self.assertTrue(result["passed"])
        self.assertTrue(result["final_confirmation_required"])
        self.assertFalse(result["can_upload"])
        self.assertFalse(result["can_start_print"])
        self.assertEqual(result["checked_at"], "2026-07-26T12:04:00Z")

    def test_reports_failed_capability_check(self) -> None:
        self.checks["capabilities_match"] = False
        result = self.evaluate()
        self.assertFalse(result["passed"])
        self.assertIn("capabilities_match", result["failed_checks"])

    def test_rejects_missing_check(self) -> None:
        self.checks.pop("connected")
        with self.assertRaises(LivePrinterCheckError):
            self.evaluate()

    def test_rejects_invalid_freshness_window(self) -> None:
        with self.assertRaisesRegex(LivePrinterCheckError, "expiry"):
            self.service.evaluate(
                provider_id="provider:custom-printer",
                artifact_digest="a" * 64,
                checks=self.checks,
                checked_at="2026-07-26T12:04:00Z",
                expires_at="2026-07-26T12:04:00Z",
            )


if __name__ == "__main__":
    unittest.main()
