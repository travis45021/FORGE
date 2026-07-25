"""Behavior and schema tests for FAS-009 policy-bundle governance."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.policy_bundles import (  # noqa: E402
    PolicyBundleError,
    PolicyBundleRegistry,
    content_digest,
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas009PolicyBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = load_json(
            ROOT / "examples" / "fas" / "policy-bundle-production.example.json"
        )
        self.registry = PolicyBundleRegistry()
        self.actor = {
            "actor_id": "forge-user:travis",
            "actor_type": "admin",
            "role": "forge_admin",
        }
        self.approvals = [
            {
                "approval_id": "forge-approval:architect-1",
                "approval_type": "forge.approval.architect",
                "approved_at": "2026-07-25T19:00:00Z",
                "expires_at": "2026-07-26T19:00:00Z",
                "verified": True,
            },
            {
                "approval_id": "forge-approval:council-1",
                "approval_type": "forge.approval.ai_council",
                "approved_at": "2026-07-25T19:01:00Z",
                "expires_at": "2026-07-26T19:00:00Z",
                "verified": True,
            },
        ]

    def activate(self, bundle_id: str | None = None) -> dict:
        return self.registry.activate(
            bundle_id or self.bundle["bundle_id"],
            channel="production",
            actor=self.actor,
            approvals=self.approvals,
            sentinel_state="clear",
            constitution_verified=True,
            evaluated_at="2026-07-25T20:30:00Z",
        )

    def test_example_digest_is_exact(self) -> None:
        self.assertEqual(self.bundle["content_digest"], content_digest(self.bundle))

    def test_register_and_activate_atomically(self) -> None:
        self.registry.register(self.bundle)
        result = self.activate()
        self.assertEqual("activated", result["action"])
        self.assertEqual(
            self.bundle["bundle_id"],
            self.registry.active_bundle("production")["bundle_id"],
        )

    def test_registered_identifier_is_immutable(self) -> None:
        self.registry.register(self.bundle)
        changed = deepcopy(self.bundle)
        changed["version"] = "1.0.1"
        changed["content_digest"] = content_digest(changed)
        with self.assertRaisesRegex(PolicyBundleError, "immutable"):
            self.registry.register(changed)

    def test_tampered_bundle_is_rejected(self) -> None:
        changed = deepcopy(self.bundle)
        changed["rollout"]["maximum_percent"] = 50
        with self.assertRaisesRegex(PolicyBundleError, "content_digest"):
            self.registry.register(changed)

    def test_unverified_signature_is_rejected(self) -> None:
        changed = deepcopy(self.bundle)
        changed["signatures"][0]["verified"] = False
        with self.assertRaisesRegex(PolicyBundleError, "verified bundle signature"):
            self.registry.register(changed)

    def test_sentinel_or_constitution_blocks_activation(self) -> None:
        self.registry.register(self.bundle)
        for sentinel_state, constitution_verified in (
            ("blocked", True),
            ("clear", False),
        ):
            with self.subTest(
                sentinel_state=sentinel_state,
                constitution_verified=constitution_verified,
            ):
                with self.assertRaises(PolicyBundleError):
                    self.registry.activate(
                        self.bundle["bundle_id"],
                        channel="production",
                        actor=self.actor,
                        approvals=self.approvals,
                        sentinel_state=sentinel_state,
                        constitution_verified=constitution_verified,
                        evaluated_at="2026-07-25T20:30:00Z",
                    )

    def test_only_forge_admin_activates(self) -> None:
        self.registry.register(self.bundle)
        actor = {**self.actor, "actor_type": "architect", "role": "forge_architect"}
        with self.assertRaisesRegex(PolicyBundleError, "Forge Admin"):
            self.registry.activate(
                self.bundle["bundle_id"],
                channel="production",
                actor=actor,
                approvals=self.approvals,
                sentinel_state="clear",
                constitution_verified=True,
                evaluated_at="2026-07-25T20:30:00Z",
            )

    def test_missing_or_duplicate_approval_is_rejected(self) -> None:
        self.registry.register(self.bundle)
        with self.assertRaisesRegex(PolicyBundleError, "ai_council"):
            self.registry.activate(
                self.bundle["bundle_id"],
                channel="production",
                actor=self.actor,
                approvals=[self.approvals[0], self.approvals[0]],
                sentinel_state="clear",
                constitution_verified=True,
                evaluated_at="2026-07-25T20:30:00Z",
            )

    def test_unknown_hardware_is_not_enumerated_by_bundle(self) -> None:
        policy_refs = self.bundle["policies"]
        self.assertTrue(all("printer" not in item for item in policy_refs))
        self.registry.register(self.bundle)
        self.assertEqual("activated", self.activate()["action"])

    def test_repeat_activation_is_idempotent_noop(self) -> None:
        self.registry.register(self.bundle)
        self.activate()
        result = self.activate()
        self.assertEqual("activation_noop", result["action"])
        self.assertEqual(2, len(self.registry.history()))

    def test_rollback_requires_registered_ancestor(self) -> None:
        first = deepcopy(self.bundle)
        second = deepcopy(self.bundle)
        second["bundle_id"] = "forge-policy-bundle:production-1.1.0"
        second["version"] = "1.1.0"
        second["parent_bundle_id"] = first["bundle_id"]
        second["content_digest"] = content_digest(second)
        self.registry.register(first)
        self.registry.register(second)
        self.activate(first["bundle_id"])
        self.activate(second["bundle_id"])
        result = self.registry.rollback(
            channel="production",
            target_bundle_id=first["bundle_id"],
            actor=self.actor,
            approvals=self.approvals,
            sentinel_state="clear",
            constitution_verified=True,
            evaluated_at="2026-07-25T21:00:00Z",
        )
        self.assertEqual("rolled_back", result["action"])
        self.assertEqual(second["bundle_id"], result["rolled_back_from"])

    def test_policy_bundle_schema(self) -> None:
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError as exc:
            self.skipTest(f"optional jsonschema validator unavailable: {exc}")
        schema = load_json(ROOT / "schemas" / "fas" / "policy-bundle.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).validate(self.bundle)


if __name__ == "__main__":
    unittest.main()
