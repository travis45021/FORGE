import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.updates import UpdateError, UpdateManager


class Fas036UpdateTests(unittest.TestCase):
    def setUp(self):
        self.manager = UpdateManager()
        self.manifest = {
            "update_id": "update:001",
            "component": "forge-core",
            "version": "1.1.0",
            "minimum_runtime": "1.0.0",
            "digest": "sha256:" + "a" * 64,
            "rollback_version": "1.0.0",
        }

    def test_compatible_update_is_not_install_authorized(self):
        self.manager.plan(
            self.manifest, current_version="1.0.0", approval_reference="decision:update"
        )
        result = self.manager.compatibility(
            "update:001",
            runtime_version="1.2.0",
            backup_verified=True,
            tests_passed=True,
        )
        self.assertEqual("ready_for_user_install", result["status"])
        self.assertFalse(result["install_authorized"])

    def test_failed_gate_blocks_update(self):
        self.manager.plan(
            self.manifest, current_version="1.0.0", approval_reference="decision:update"
        )
        result = self.manager.compatibility(
            "update:001",
            runtime_version="1.2.0",
            backup_verified=False,
            tests_passed=True,
        )
        self.assertEqual("blocked", result["status"])

    def test_rollback_requires_user_approval(self):
        self.manager.plan(
            self.manifest, current_version="1.0.0", approval_reference="decision:update"
        )
        with self.assertRaises(UpdateError):
            self.manager.rollback(
                "update:001", reason="failed test", user_approved=False
            )
        result = self.manager.rollback(
            "update:001", reason="failed test", user_approved=True
        )
        self.assertEqual("rollback_planned", result["status"])

    def test_update_manifest_and_runtime_versions_are_strict(self):
        invalid = dict(self.manifest)
        invalid["digest"] = "sha256:short"
        with self.assertRaisesRegex(UpdateError, "digest"):
            self.manager.plan(
                invalid, current_version="1.0.0", approval_reference="decision:update"
            )
        self.manager.plan(
            self.manifest, current_version="1.0.0", approval_reference="decision:update"
        )
        with self.assertRaisesRegex(UpdateError, "versions"):
            self.manager.compatibility(
                "update:001",
                runtime_version="not-a-version",
                backup_verified=True,
                tests_passed=True,
            )

    def test_update_identity_and_rollback_reason_are_strict(self):
        self.manager.plan(
            self.manifest,
            current_version="1.0.0",
            approval_reference="decision:update",
        )
        with self.assertRaisesRegex(UpdateError, "identity"):
            self.manager.plan(
                self.manifest,
                current_version="1.0.0",
                approval_reference="decision:update-again",
            )
        with self.assertRaisesRegex(UpdateError, "reason"):
            self.manager.rollback("update:001", reason=42, user_approved=True)


if __name__ == "__main__":
    unittest.main()
