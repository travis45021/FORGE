"""Behavior tests for the FAS-008 reference authorization evaluator."""

from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.authorization import AuthorizationEngine


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas008AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = AuthorizationEngine()
        cls.policy = load_json(
            ROOT / "examples" / "fas" / "policy-print-start.example.json"
        )
        cls.request = load_json(
            ROOT / "examples" / "fas" / "authorization-request-print-start.example.json"
        )
        cls.expected_result = load_json(
            ROOT / "examples" / "fas" / "authorization-result-allow.example.json"
        )

    def test_approved_user_directed_action_is_allowed(self) -> None:
        result = self.engine.evaluate(self.request, [self.policy])
        self.assertEqual("allow", result["outcome"])
        self.assertEqual(
            self.request["requested_action"],
            result["effective_action"],
        )

    def test_published_result_matches_reference_evaluator(self) -> None:
        result = self.engine.evaluate(self.request, [self.policy])
        self.assertEqual(self.expected_result, result)

    def test_repeated_input_has_stable_evaluation_identity(self) -> None:
        first = self.engine.evaluate(self.request, [self.policy])
        second = self.engine.evaluate(self.request, [deepcopy(self.policy)])
        self.assertEqual(first["evaluation_id"], second["evaluation_id"])
        self.assertEqual(first["policy_set_digest"], second["policy_set_digest"])

    def test_missing_approval_requires_challenge(self) -> None:
        request = deepcopy(self.request)
        request["approvals"] = []
        result = self.engine.evaluate(request, [self.policy])
        self.assertEqual("challenge", result["outcome"])
        self.assertEqual("required_approval_missing", result["reason_codes"][0])
        self.assertEqual(1, result["missing_approvals"][0]["minimum_count"])

    def test_expired_approval_requires_challenge(self) -> None:
        request = deepcopy(self.request)
        request["approvals"][0]["expires_at"] = "2026-07-25T17:59:59Z"
        result = self.engine.evaluate(request, [self.policy])
        self.assertEqual("challenge", result["outcome"])

    def test_explicit_deny_overrides_allow(self) -> None:
        deny = deepcopy(self.policy)
        deny["policy_id"] = "forge-policy:emergency-print-start-deny"
        deny["effect"] = "deny"
        result = self.engine.evaluate(self.request, [self.policy, deny])
        self.assertEqual("deny", result["outcome"])
        self.assertIn("explicit_deny", result["reason_codes"])

    def test_unknown_action_fails_closed(self) -> None:
        request = deepcopy(self.request)
        request["requested_action"]["action_type"] = "user.print.custom_sequence"
        result = self.engine.evaluate(request, [self.policy])
        self.assertEqual("deny", result["outcome"])
        self.assertIn("no_applicable_allow_policy", result["reason_codes"])

    def test_unknown_hardware_target_does_not_require_code_change(self) -> None:
        request = deepcopy(self.request)
        request["requested_action"]["target_refs"] = [
            "user-printer:experimental-corexy-01"
        ]
        result = self.engine.evaluate(request, [self.policy])
        self.assertEqual("allow", result["outcome"])

    def test_sentinel_block_cannot_be_overridden(self) -> None:
        request = deepcopy(self.request)
        request["facts"]["sentinel_state"] = "blocked"
        result = self.engine.evaluate(request, [self.policy])
        self.assertEqual("deny", result["outcome"])
        self.assertEqual(["sentinel_block"], result["reason_codes"])

    def test_arl5_is_admin_only(self) -> None:
        request = deepcopy(self.request)
        request["readiness_level"] = 5
        policy = deepcopy(self.policy)
        policy["minimum_readiness_level"] = 0
        policy["maximum_readiness_level"] = 5
        result = self.engine.evaluate(request, [policy])
        self.assertEqual("deny", result["outcome"])
        self.assertEqual(["arl5_admin_only"], result["reason_codes"])

    def test_arl2_through_4_are_restricted(self) -> None:
        request = deepcopy(self.request)
        request["readiness_level"] = 3
        policy = deepcopy(self.policy)
        policy["minimum_readiness_level"] = 0
        policy["maximum_readiness_level"] = 5
        result = self.engine.evaluate(request, [policy])
        self.assertEqual("deny", result["outcome"])
        self.assertEqual(["restricted_arl_unavailable"], result["reason_codes"])

    def test_unapproved_or_unsigned_decision_cannot_execute(self) -> None:
        for field, value in (
            ("disposition", "proposed"),
            ("signature_verified", False),
            ("superseded", True),
            ("revoked", True),
        ):
            with self.subTest(field=field):
                request = deepcopy(self.request)
                request["decision_state"][field] = value
                result = self.engine.evaluate(request, [self.policy])
                self.assertEqual("deny", result["outcome"])

    def test_parameter_reject_constraint_blocks_out_of_bounds_value(self) -> None:
        request = deepcopy(self.request)
        request["requested_action"]["parameters"]["nozzle_temperature_c"] = 301
        result = self.engine.evaluate(request, [self.policy])
        self.assertEqual("deny", result["outcome"])
        self.assertIn("parameter_outside_policy_bounds", result["reason_codes"])

    def test_clamp_is_visible_in_effective_action(self) -> None:
        request = deepcopy(self.request)
        request["requested_action"]["parameters"]["nozzle_temperature_c"] = 301
        policy = deepcopy(self.policy)
        policy["parameter_constraints"][0]["on_violation"] = "clamp"
        result = self.engine.evaluate(request, [policy])
        self.assertEqual("allow", result["outcome"])
        self.assertEqual(
            300,
            result["effective_action"]["parameters"]["nozzle_temperature_c"],
        )
        self.assertEqual(301, result["applied_constraints"][0]["requested_value"])

    def test_policy_input_is_not_mutated(self) -> None:
        request = deepcopy(self.request)
        policy = deepcopy(self.policy)
        original_request = deepcopy(request)
        original_policy = deepcopy(policy)
        self.engine.evaluate(request, [policy])
        self.assertEqual(original_request, request)
        self.assertEqual(original_policy, policy)


if __name__ == "__main__":
    unittest.main()
