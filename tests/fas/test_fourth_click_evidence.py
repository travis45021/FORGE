"""Integration tests for evidence-backed fourth-click confirmation."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.job_lifecycle import JobLifecycleError, PrintJobLifecycle


class FourthClickEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lifecycle = PrintJobLifecycle()
        self.digest = "a" * 64
        self.lifecycle.create(
            {
                "job_id": "job-1",
                "artifact_id": "artifact-1",
                "artifact_digest": self.digest,
                "provider_id": "provider-1",
                "state": "draft",
                "preflight_passed": True,
                "live_checks_passed": False,
                "click_count": 0,
            }
        )
        self.lifecycle.transition("job-1", "validated", reason="validated")
        for action in ("upload", "configure", "review"):
            self.lifecycle.click("job-1", action=action, actor="user-1")
        self.acceptance = {
            "artifact_digest": self.digest,
            "final_confirmation_required": True,
            "preflight_verified": True,
            "can_upload": False,
            "can_start_print": False,
        }
        self.live = {
            "provider_id": "provider-1",
            "artifact_digest": self.digest,
            "passed": True,
            "can_upload": False,
            "can_start_print": False,
        }

    def confirm(self) -> dict:
        return self.lifecycle.final_confirm_with_evidence(
            "job-1",
            actor="user-1",
            confirmation=True,
            acceptance=self.acceptance,
            live_checks=self.live,
            authorization_verified=True,
        )

    def test_fourth_click_accepts_matching_evidence(self) -> None:
        job = self.confirm()
        self.assertEqual(job["state"], "upload_pending")
        self.assertEqual(job["final_confirmed_by"], "user-1")

    def test_rejects_stale_artifact_checks(self) -> None:
        self.live["artifact_digest"] = "b" * 64
        with self.assertRaises(JobLifecycleError):
            self.confirm()

    def test_rejects_failed_live_checks(self) -> None:
        self.live["passed"] = False
        with self.assertRaises(JobLifecycleError):
            self.confirm()

    def test_rejects_acceptance_without_preflight(self) -> None:
        self.acceptance["preflight_verified"] = False
        with self.assertRaises(JobLifecycleError):
            self.confirm()


if __name__ == "__main__":
    unittest.main()
