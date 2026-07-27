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
        self.input_digest = "b" * 64
        self.profile_digest = "c" * 64
        self.engine_source_digest = "d" * 64
        self.engine_build_digest = "e" * 64
        self.comparison_digest = "f" * 64
        self.lifecycle.create(
            {
                "job_id": "job-1",
                "artifact_id": "artifact-1",
                "artifact_digest": self.digest,
                "input_digest": self.input_digest,
                "profile_digest": self.profile_digest,
                "engine_source_digest": self.engine_source_digest,
                "engine_build_digest": self.engine_build_digest,
                "comparison_id": "comparison-1",
                "comparison_evidence_digest": self.comparison_digest,
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
            "input_digest": self.input_digest,
            "profile_digest": self.profile_digest,
            "engine_source_digest": self.engine_source_digest,
            "engine_build_digest": self.engine_build_digest,
            "comparison_id": "comparison-1",
            "comparison_evidence_digest": self.comparison_digest,
            "reviewed_by": "reviewer-1",
            "reviewed_at": "2026-07-26T12:00:00Z",
            "final_confirmation_required": True,
            "preflight_verified": True,
            "pair_preflight_verified": True,
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
            confirmed_at="2026-07-26T12:05:00Z",
            confirmation=True,
            acceptance=self.acceptance,
            live_checks=self.live,
            authorization_verified=True,
        )

    def test_fourth_click_accepts_matching_evidence(self) -> None:
        job = self.confirm()
        self.assertEqual(job["state"], "upload_pending")
        self.assertEqual(job["final_confirmed_by"], "user-1")
        self.assertEqual(job["final_confirmed_at"], "2026-07-26T12:05:00Z")
        self.assertTrue(job["artifact_preflight_verified"])
        self.assertTrue(job["artifact_pair_preflight_verified"])
        self.assertEqual(job["comparison_reviewed_by"], "reviewer-1")
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

    def test_rejects_acceptance_without_pair_preflight(self) -> None:
        self.acceptance["pair_preflight_verified"] = False
        with self.assertRaisesRegex(JobLifecycleError, "coordinated pair"):
            self.confirm()

    def test_rejects_acceptance_from_different_profile(self) -> None:
        self.acceptance["profile_digest"] = "d" * 64
        with self.assertRaisesRegex(JobLifecycleError, "profile digest"):
            self.confirm()

    def test_rejects_acceptance_from_different_engine_build(self) -> None:
        self.acceptance["engine_build_digest"] = "f" * 64
        with self.assertRaisesRegex(JobLifecycleError, "engine build digest"):
            self.confirm()

    def test_rejects_acceptance_without_review_attribution(self) -> None:
        self.acceptance["reviewed_by"] = ""
        with self.assertRaisesRegex(JobLifecycleError, "click-three attribution"):
            self.confirm()

    def test_rejects_review_timestamp_after_final_confirmation(self) -> None:
        self.acceptance["reviewed_at"] = "2026-07-26T12:06:00Z"
        with self.assertRaisesRegex(JobLifecycleError, "after final confirmation"):
            self.confirm()


if __name__ == "__main__":
    unittest.main()
