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
            "artifact_digest": "a" * 64,
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
        self.assertFalse(result["physical_dispatch_allowed"])

    def test_rejects_job_before_final_confirmation(self) -> None:
        self.job["state"] = "final_confirmation_required"
        with self.assertRaises(TransportError):
            self.prepare()

    def test_rejects_missing_runtime_lease(self) -> None:
        with self.assertRaises(TransportError):
            self.registry.prepare_artifact_upload(
                "provider:custom",
                self.job,
                runtime_lease_active=False,
                authorization_verified=True,
            )


if __name__ == "__main__":
    unittest.main()
