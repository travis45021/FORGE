import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.job_lifecycle import JobLifecycleError, PrintJobLifecycle


class Fas034JobLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.service = PrintJobLifecycle()
        self.job = {
            "job_id": "job:001",
            "artifact_id": "artifact:001",
            "provider_id": "provider:printer",
            "state": "draft",
            "preflight_passed": True,
            "live_checks_passed": False,
            "click_count": 0,
        }
        self.service.create(self.job)
        self.service.transition("job:001", "validated", reason="preflight passed")
        self.service.transition("job:001", "ready", reason="sliced and reviewed")

    def test_four_click_boundary(self):
        for action in ("configure", "review", "upload"):
            self.service.click("job:001", action=action, actor="forge-user:local")
        with self.assertRaises(JobLifecycleError):
            self.service.final_confirm(
                "job:001",
                actor="forge-user:local",
                confirmed_at="2026-07-26T12:05:00Z",
                confirmation=True,
                live_checks_passed=False,
                authorization_verified=True,
            )
        result = self.service.final_confirm(
            "job:001",
            actor="forge-user:local",
            confirmed_at="2026-07-26T12:05:00Z",
            confirmation=True,
            live_checks_passed=True,
            authorization_verified=True,
        )
        self.assertEqual("upload_pending", result["state"])
        self.assertEqual("2026-07-26T12:05:00Z", result["final_confirmed_at"])

    def test_final_confirmation_requires_three_clicks(self):
        self.service.click("job:001", action="review", actor="forge-user:local")
        with self.assertRaises(JobLifecycleError):
            self.service.final_confirm(
                "job:001",
                actor="forge-user:local",
                confirmed_at="2026-07-26T12:05:00Z",
                confirmation=True,
                live_checks_passed=True,
                authorization_verified=True,
            )


if __name__ == "__main__":
    unittest.main()
