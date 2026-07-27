"""Reference canonicalization and hash-chain tests for FAS-007."""

from __future__ import annotations

import hashlib
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "fas" / "decision-approved.example.json"


def canonical_payload(record: dict) -> bytes:
    payload = deepcopy(record)
    payload.pop("record_hash", None)
    signature = payload.get("signature")
    if isinstance(signature, dict):
        signature.pop("value", None)
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def record_hash(record: dict) -> str:
    return f"sha256:{hashlib.sha256(canonical_payload(record)).hexdigest()}"


class Fas007IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with EXAMPLE.open("r", encoding="utf-8") as stream:
            cls.record = json.load(stream)

    def test_hashing_is_deterministic(self) -> None:
        reordered = dict(reversed(list(self.record.items())))
        self.assertEqual(record_hash(self.record), record_hash(reordered))

    def test_material_change_changes_hash(self) -> None:
        changed = deepcopy(self.record)
        changed["disposition"] = "blocked"
        self.assertNotEqual(record_hash(self.record), record_hash(changed))

    def test_signature_value_is_not_self_referential(self) -> None:
        changed = deepcopy(self.record)
        changed["signature"]["value"] = "A_DIFFERENT_EXAMPLE_SIGNATURE"
        self.assertEqual(record_hash(self.record), record_hash(changed))

    def test_previous_hash_participates_in_digest(self) -> None:
        changed = deepcopy(self.record)
        changed["previous_record_hash"] = (
            "sha256:1111111111111111111111111111111111111111111111111111111111111111"
        )
        self.assertNotEqual(record_hash(self.record), record_hash(changed))


if __name__ == "__main__":
    unittest.main()
