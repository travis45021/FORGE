"""Tests for the post-confirmation controlled-upload handoff."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.transport import HardwareTransportRegistry, TransportError


class ControlledUploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = HardwareTransportRegistry()
        self.registry.register(
            {
                "provider_id": "provider:custom",
                "transport": "local-capability-provider",
                "capabilities": ["artifact.upload"],
                "state": "registered",
                "health": "healthy",
            }
        )
        self.job = {
            "job_id": "job-1",
            "provider_id": "provider:custom",
            "state": "upload_pending",
            "click_count": 3,
            "final_confirmed_by": "user-1",
            "final_confirmed_at": "2026-07-26T12:05:00Z",
            "confirmation_expires_at": "2026-07-26T12:10:00Z",
            "confirmation_token": "confirmation-" + ("x" * 32),
            "artifact_digest": "a" * 64,
            "input_digest": "b" * 64,
            "profile_digest": "c" * 64,
            "engine_source_digest": "d" * 64,
            "engine_build_digest": "e" * 64,
            "comparison_id": "comparison-1",
            "comparison_evidence_digest": "f" * 64,
            "comparison_reviewed_by": "reviewer-1",
            "comparison_reviewed_at": "2026-07-26T12:00:00Z",
            "artifact_preflight_verified": True,
            "artifact_pair_preflight_verified": True,
        }

    def prepare(self) -> dict:
        return self.registry.prepare_artifact_upload(
            "provider:custom",
            self.job,
            runtime_lease_active=True,
            authorization_verified=True,
        )

    def test_prepares_non_dispatching_handoff_after_fourth_click(self) -> None:
        result = self.prepare()
        self.assertTrue(result["fourth_click_satisfied"])
        self.assertTrue(result["artifact_pair_preflight_verified"])
        self.assertEqual(result["input_digest"], "b" * 64)
        self.assertEqual(result["profile_digest"], "c" * 64)
        self.assertEqual(result["engine_build_digest"], "e" * 64)
        self.assertEqual(result["comparison_evidence_digest"], "f" * 64)
        self.assertEqual(result["comparison_reviewed_by"], "reviewer-1")
        self.assertEqual(result["confirmed_at"], "2026-07-26T12:05:00Z")
        self.assertEqual(result["confirmation_expires_at"], "2026-07-26T12:10:00Z")
        self.assertFalse(result["physical_dispatch_allowed"])

    def test_rejects_job_before_final_confirmation(self) -> None:
        self.job["state"] = "final_confirmation_required"
        with self.assertRaises(TransportError):
            self.prepare()

    def test_rejects_job_without_final_confirmation_time(self) -> None:
        self.job["final_confirmed_at"] = ""
        with self.assertRaisesRegex(TransportError, "fourth click"):
            self.prepare()

    def test_rejects_missing_runtime_lease(self) -> None:
        with self.assertRaises(TransportError):
            self.registry.prepare_artifact_upload(
                "provider:custom",
                self.job,
                runtime_lease_active=False,
                authorization_verified=True,
            )

    def test_rejects_job_without_fresh_confirmation_token(self) -> None:
        self.job.pop("confirmation_token")
        with self.assertRaises(TransportError):
            self.prepare()

    def test_rejects_job_without_artifact_preflight(self) -> None:
        self.job["artifact_preflight_verified"] = False
        with self.assertRaises(TransportError):
            self.prepare()

    def test_rejects_job_without_pair_preflight(self) -> None:
        self.job["artifact_pair_preflight_verified"] = False
        with self.assertRaisesRegex(TransportError, "coordinated pair"):
            self.prepare()

    def test_rejects_job_without_profile_lineage(self) -> None:
        self.job.pop("profile_digest")
        with self.assertRaisesRegex(TransportError, "profile digest"):
            self.prepare()

    def test_rejects_job_without_engine_build_provenance(self) -> None:
        self.job.pop("engine_build_digest")
        with self.assertRaisesRegex(TransportError, "engine build digest"):
            self.prepare()

    def test_rejects_job_without_reviewed_comparison(self) -> None:
        self.job.pop("comparison_evidence_digest")
        with self.assertRaisesRegex(TransportError, "comparison evidence digest"):
            self.prepare()

    def test_rejects_job_without_review_attribution(self) -> None:
        self.job.pop("comparison_reviewed_at")
        with self.assertRaisesRegex(TransportError, "review attribution"):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
