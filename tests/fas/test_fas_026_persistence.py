import hashlib
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.persistence import (
    AtomicSnapshotStore,
    DataRecoveryService,
    PersistenceError,
)


def digest(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def record(record_id, value, data_class="durable_local", authoritative=True):
    return {
        "record_id": record_id,
        "schema_version": "1.0.0",
        "owner_scope": "forge-user:local",
        "data_class": data_class,
        "value": value,
        "authoritative": authoritative,
        "created_at": "2026-07-26T12:00:00Z",
        "updated_at": "2026-07-26T12:00:00Z",
        "retention_class": "user-selected",
        "provenance_refs": ["forge-event:data-created"],
        "digest": digest(value),
    }


class Fas026PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.service = DataRecoveryService()
        self.profile = record(
            "forge-record:profile-default",
            {"profile": "default", "version": 1},
        )
        self.state = record(
            "forge-record:context-001",
            {"mission": "print-001", "state": "paused"},
            data_class="operational_state",
            authoritative=False,
        )
        self.secret = record(
            "forge-record:printer-token",
            {"token": "private"},
            data_class="secret",
            authoritative=False,
        )
        for item in (self.profile, self.state, self.secret):
            self.service.put(item)

    def backup(self):
        return self.service.create_backup(
            "forge-backup:local-001",
            owner_scope="forge-user:local",
            selected_classes=["durable_local", "operational_state", "secret"],
            destination="file:local-backups/forge-backup-local-001",
            encrypted=True,
            created_at="2026-07-26T12:05:00Z",
            retention_class="user-selected",
            include_secrets=False,
        )

    def test_records_require_provenance_and_integrity(self):
        stored = self.service.record(self.profile["record_id"])
        self.assertEqual(self.profile, stored)
        invalid = deepcopy(self.profile)
        invalid["digest"] = digest({"changed": True})
        with self.assertRaisesRegex(PersistenceError, "digest"):
            self.service.put(invalid)

    def test_secret_data_is_excluded_by_default(self):
        exported = self.service.export(owner_scope="forge-user:local")
        self.assertFalse(exported["secrets_included"])
        self.assertNotIn(
            self.secret["record_id"],
            {item["record_id"] for item in exported["records"]},
        )
        manifest = self.backup()
        self.assertFalse(manifest["includes_secrets"])
        self.assertNotIn(self.secret["record_id"], manifest["included_record_ids"])

    def test_secret_backup_requires_confirmation_and_encryption(self):
        with self.assertRaisesRegex(PersistenceError, "confirmation"):
            self.service.create_backup(
                "forge-backup:secret-001",
                owner_scope="forge-user:local",
                selected_classes=["secret"],
                destination="file:secret",
                encrypted=True,
                created_at="2026-07-26T12:05:00Z",
                retention_class="restricted",
                include_secrets=True,
            )
        with self.assertRaisesRegex(PersistenceError, "encrypted"):
            self.service.create_backup(
                "forge-backup:secret-002",
                owner_scope="forge-user:local",
                selected_classes=["secret"],
                destination="file:secret",
                encrypted=False,
                created_at="2026-07-26T12:05:00Z",
                retention_class="restricted",
                include_secrets=True,
                secrets_confirmed=True,
            )

    def test_backup_verification_detects_tampering(self):
        self.backup()
        verified = self.service.verify_backup("forge-backup:local-001")
        self.assertEqual("verified", verified["status"])
        self.service._backup_payloads["forge-backup:local-001"][0]["value"] = {
            "tampered": True
        }
        with self.assertRaisesRegex(PersistenceError, "integrity"):
            self.service.verify_backup("forge-backup:local-001")

    def test_restore_is_review_only_and_never_replays_physical_work(self):
        self.backup()
        inspected = self.service.restore(
            "forge-backup:local-001",
            mode="inspect_only",
            requested_at="2026-07-26T12:10:00Z",
            reason="user requested inspection",
        )
        self.assertEqual([], inspected["applied_record_ids"])
        self.assertEqual(
            {self.profile["record_id"], self.state["record_id"]},
            set(inspected["inspected_record_ids"]),
        )
        self.assertFalse(inspected["hardware_resume_allowed"])
        self.assertFalse(inspected["physical_commands_replayed"])
        self.assertTrue(inspected["requires_live_reverification"])
        self.assertTrue(inspected["requires_user_review"])

    def test_selected_restore_preserves_conflicts(self):
        self.backup()
        changed = deepcopy(self.profile)
        changed["value"] = {"profile": "changed"}
        changed["digest"] = digest(changed["value"])
        self.service._records[self.profile["record_id"]] = changed
        result = self.service.restore(
            "forge-backup:local-001",
            mode="selected_records",
            selected_record_ids=[self.profile["record_id"]],
            requested_at="2026-07-26T12:10:00Z",
            reason="user requested profile recovery",
        )
        self.assertEqual([self.profile["record_id"]], result["conflicts"])
        self.assertEqual(changed, self.service.record(self.profile["record_id"]))

    def test_migration_requires_verified_backup_and_user_approval(self):
        self.backup()
        plan = self.service.migration_plan(
            from_version="1.0.0",
            to_version="1.1.0",
            created_at="2026-07-26T12:15:00Z",
            backup_id="forge-backup:local-001",
        )
        self.assertTrue(plan["requires_backup"])
        self.assertTrue(plan["requires_user_approval"])
        with self.assertRaisesRegex(PersistenceError, "unknown backup"):
            self.service.migration_plan(
                from_version="1.0.0",
                to_version="1.1.0",
                created_at="2026-07-26T12:15:00Z",
                backup_id="forge-backup:missing",
            )

    def test_service_has_no_authority_or_hardware_surface(self):
        self.assertFalse(hasattr(self.service, "authorize"))
        self.assertFalse(hasattr(self.service, "dispatch"))
        self.assertFalse(hasattr(self.service, "resume_print"))

    def test_schema_and_examples_validate(self):
        from jsonschema import Draft202012Validator, FormatChecker

        for schema_name, example_name in (
            ("data-record.schema.json", "data-record-profile.example.json"),
            ("backup-manifest.schema.json", "backup-manifest-local.example.json"),
            ("restore-plan.schema.json", "restore-plan-safe.example.json"),
        ):
            schema = json.loads(
                (ROOT / "schemas/fas" / schema_name).read_text(encoding="utf-8")
            )
            example = json.loads(
                (ROOT / "examples/fas" / example_name).read_text(encoding="utf-8")
            )
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(
                example
            )

    def test_filesystem_snapshot_is_atomic_and_integrity_checked(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state" / "forge.json"
            snapshot = self.service.export(owner_scope="forge-user:local")
            store = AtomicSnapshotStore()
            store.write(path, snapshot)
            self.assertEqual(snapshot, store.read(path))
            path.write_text(
                path.read_text(encoding="utf-8").replace("profile", "tampered"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PersistenceError, "integrity"):
                store.read(path)

    def test_filesystem_snapshot_rejects_secret_export(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            snapshot = self.service.export(
                owner_scope="forge-user:local", include_secrets=True
            )
            with self.assertRaisesRegex(PersistenceError, "secrets"):
                AtomicSnapshotStore().write(Path(directory) / "state.json", snapshot)


if __name__ == "__main__":
    unittest.main()
