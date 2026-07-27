"""Local ownership, persistence, backup, and recovery for canonical FAS-026."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


class PersistenceError(ValueError):
    """Raised when local data or recovery operations violate FAS-026."""


DATA_CLASSES = {
    "ephemeral",
    "operational_state",
    "durable_local",
    "audit",
    "evidence",
    "secret",
}
RESTORE_MODES = {
    "inspect_only",
    "selected_records",
    "configuration_and_profiles",
    "full_workspace",
    "runtime_recovery_review",
}


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PersistenceError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PersistenceError(f"invalid timestamp: {value}") from exc


def _digest(value: Any) -> str:
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PersistenceError("persisted values must be JSON-compatible") from exc
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


class AtomicSnapshotStore:
    """Crash-atomic JSON snapshot store for non-secret local records."""

    def write(self, path: str | Path, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(snapshot))
        if item.get("secrets_included") is True:
            raise PersistenceError("filesystem snapshots cannot contain secrets")
        if item.get("export_digest") != _digest(item.get("records")):
            raise PersistenceError("snapshot digest does not match records")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(
            item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=target.parent, prefix=f".{target.name}.", delete=False
            ) as handle:
                temporary = handle.name
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
            temporary = None
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
        return deepcopy(item)

    def read(self, path: str | Path) -> dict[str, Any]:
        try:
            item = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PersistenceError("snapshot cannot be read") from exc
        if not isinstance(item, dict) or item.get("secrets_included") is True:
            raise PersistenceError("snapshot is invalid or contains secrets")
        records = item.get("records")
        if not isinstance(records, list) or item.get("export_digest") != _digest(
            records
        ):
            raise PersistenceError("snapshot integrity verification failed")
        return deepcopy(item)


class DataRecoveryService:
    """Deterministic local reference store with replay-safe recovery."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._backups: dict[str, dict[str, Any]] = {}
        self._backup_payloads: dict[str, list[dict[str, Any]]] = {}
        self._history: list[dict[str, Any]] = []

    def put(self, record: Mapping[str, Any]) -> dict[str, Any]:
        candidate = deepcopy(dict(record))
        self._validate_record(candidate)
        record_id = candidate["record_id"]
        existing = self._records.get(record_id)
        if existing is not None and existing["digest"] != candidate["digest"]:
            raise PersistenceError("record identity is immutable; create a new version")
        self._records[record_id] = candidate
        self._record("data.record.stored", record_id, candidate["data_class"])
        return deepcopy(candidate)

    def record(self, record_id: str) -> dict[str, Any] | None:
        item = self._records.get(record_id)
        return deepcopy(item) if item else None

    def records(self, *, data_class: str | None = None) -> list[dict[str, Any]]:
        return [
            deepcopy(self._records[key])
            for key in sorted(self._records)
            if data_class is None or self._records[key]["data_class"] == data_class
        ]

    def create_backup(
        self,
        backup_id: str,
        *,
        owner_scope: str,
        selected_classes: list[str],
        destination: str,
        encrypted: bool,
        created_at: str,
        retention_class: str,
        include_secrets: bool = False,
        secrets_confirmed: bool = False,
    ) -> dict[str, Any]:
        _utc(created_at)
        if backup_id in self._backups:
            raise PersistenceError("backup identity is immutable")
        if not selected_classes or any(
            item not in DATA_CLASSES for item in selected_classes
        ):
            raise PersistenceError("backup classes must be known and non-empty")
        if include_secrets and not secrets_confirmed:
            raise PersistenceError("including secrets requires explicit confirmation")
        if include_secrets and not encrypted:
            raise PersistenceError("secret backups must be encrypted")
        selected = set(selected_classes)
        payload = [
            deepcopy(self._records[key])
            for key in sorted(self._records)
            if self._records[key]["owner_scope"] == owner_scope
            and self._records[key]["data_class"] in selected
            and (include_secrets or self._records[key]["data_class"] != "secret")
        ]
        content_digest = _digest(payload)
        manifest = {
            "backup_id": backup_id,
            "schema_version": "1.0.0",
            "owner_scope": owner_scope,
            "created_at": created_at,
            "selected_classes": sorted(selected),
            "included_record_ids": [item["record_id"] for item in payload],
            "destination": destination,
            "encrypted": encrypted,
            "includes_secrets": include_secrets,
            "source_digest": content_digest,
            "content_digest": content_digest,
            "status": "created",
            "retention_class": retention_class,
            "restore_modes": sorted(RESTORE_MODES),
        }
        self._backups[backup_id] = manifest
        self._backup_payloads[backup_id] = payload
        self._record("backup.created", backup_id, destination)
        return deepcopy(manifest)

    def verify_backup(self, backup_id: str) -> dict[str, Any]:
        manifest = self._require_backup(backup_id)
        payload = self._backup_payloads[backup_id]
        actual = _digest(payload)
        if actual != manifest["content_digest"] or actual != manifest["source_digest"]:
            manifest["status"] = "corrupt"
            self._record("data.integrity.failed", backup_id, "backup_digest_mismatch")
            raise PersistenceError("backup integrity verification failed")
        manifest["status"] = "verified"
        self._record("backup.verified", backup_id, "digest_match")
        return deepcopy(manifest)

    def restore(
        self,
        backup_id: str,
        *,
        mode: str,
        requested_at: str,
        reason: str,
        selected_record_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        _utc(requested_at)
        if mode not in RESTORE_MODES:
            raise PersistenceError("unknown restore mode")
        manifest = self.verify_backup(backup_id)
        payload = self._backup_payloads[backup_id]
        selected_ids = set(selected_record_ids or [])
        if selected_record_ids and not selected_ids <= set(
            manifest["included_record_ids"]
        ):
            raise PersistenceError("restore selection contains an unknown record")
        if mode == "selected_records" and not selected_ids:
            raise PersistenceError("selected_records restore requires record IDs")
        if mode == "inspect_only":
            candidates = payload
        elif mode == "selected_records":
            candidates = [item for item in payload if item["record_id"] in selected_ids]
        elif mode == "configuration_and_profiles":
            candidates = [
                item
                for item in payload
                if item["data_class"] in {"durable_local", "audit"}
            ]
        elif mode == "runtime_recovery_review":
            candidates = [
                item for item in payload if item["data_class"] == "operational_state"
            ]
        else:
            candidates = payload
        applied: list[str] = []
        conflicts: list[str] = []
        if mode != "inspect_only":
            for item in candidates:
                current = self._records.get(item["record_id"])
                if current is None:
                    self._records[item["record_id"]] = deepcopy(item)
                    applied.append(item["record_id"])
                elif current["digest"] != item["digest"]:
                    conflicts.append(item["record_id"])
        self._backups[backup_id]["status"] = "restored"
        manifest["status"] = "restored"
        self._record("restore.completed", backup_id, mode)
        return {
            "restore_id": f"forge-restore:{backup_id.split(':')[-1]}",
            "backup_id": backup_id,
            "mode": mode,
            "requested_at": requested_at,
            "reason": reason,
            "inspected_record_ids": [item["record_id"] for item in candidates],
            "applied_record_ids": applied,
            "conflicts": conflicts,
            "hardware_resume_allowed": False,
            "physical_commands_replayed": False,
            "requires_live_reverification": True,
            "requires_user_review": True,
        }

    def export(
        self, *, owner_scope: str, include_secrets: bool = False
    ) -> dict[str, Any]:
        records = [
            item
            for item in self.records()
            if item["owner_scope"] == owner_scope
            and (
                (include_secrets is True and item["data_class"] == "secret")
                or item["data_class"] != "secret"
            )
        ]
        return {
            "schema_version": "1.0.0",
            "owner_scope": owner_scope,
            "records": records,
            "secrets_included": include_secrets,
            "export_digest": _digest(records),
        }

    def migration_plan(
        self, *, from_version: str, to_version: str, created_at: str, backup_id: str
    ) -> dict[str, Any]:
        _utc(created_at)
        self._require_backup(backup_id)
        if from_version == to_version:
            raise PersistenceError("migration versions must differ")
        return {
            "migration_id": f"forge-migration:{from_version}-to-{to_version}",
            "from_version": from_version,
            "to_version": to_version,
            "backup_id": backup_id,
            "created_at": created_at,
            "reversible": True,
            "requires_user_approval": True,
            "requires_backup": True,
        }

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def _validate_record(self, item: Mapping[str, Any]) -> None:
        required = {
            "record_id",
            "schema_version",
            "owner_scope",
            "data_class",
            "value",
            "authoritative",
            "created_at",
            "updated_at",
            "retention_class",
            "provenance_refs",
            "digest",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise PersistenceError(f"record missing fields: {', '.join(missing)}")
        if item["data_class"] not in DATA_CLASSES:
            raise PersistenceError("unknown data class")
        if not isinstance(item["authoritative"], bool):
            raise PersistenceError("authoritative must be boolean")
        if not item["provenance_refs"]:
            raise PersistenceError("persisted records require provenance")
        _utc(item["created_at"])
        _utc(item["updated_at"])
        if item["digest"] != _digest(item["value"]):
            raise PersistenceError("record digest does not match value")
        if item["data_class"] == "secret" and item["authoritative"]:
            raise PersistenceError("secrets cannot be authoritative records")

    def _require_backup(self, backup_id: str) -> dict[str, Any]:
        try:
            return self._backups[backup_id]
        except KeyError as exc:
            raise PersistenceError(f"unknown backup: {backup_id}") from exc

    def _record(self, event_type: str, target_id: str, reason: str) -> None:
        self._history.append(
            {"event_type": event_type, "target_id": target_id, "reason": reason}
        )
