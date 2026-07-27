import json
import unittest
from pathlib import Path

from forge.fas.interfaces import InterfaceError, InterfaceGateway

ROOT = Path(__file__).resolve().parents[2]


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.received = []

        def executive(request):
            self.received.append(request)
            return {"decision": "challenge", "reason": "approval_required"}

        self.gateway = InterfaceGateway(executive)
        self.request = {
            "request_id": "req-1",
            "action": "mission.start",
            "target": "mission:1",
            "parameters": {},
        }

    def test_local_request_uses_executive_path(self):
        result = self.gateway.submit(
            self.request, authenticated_identity="user:local", api_version="v1"
        )
        self.assertEqual(result["executive_result"]["decision"], "challenge")
        self.assertEqual(self.received[0]["source"], "interface_gateway")

    def test_remote_transport_and_raw_hardware_are_rejected(self):
        with self.assertRaises(InterfaceError):
            self.gateway.submit(
                self.request,
                authenticated_identity="user:local",
                api_version="v1",
                transport="cloud",
            )
        with self.assertRaises(InterfaceError):
            self.gateway.submit(
                {**self.request, "raw_hardware_command": "G28"},
                authenticated_identity="user:local",
                api_version="v1",
            )

    def test_nested_raw_hardware_command_is_rejected(self):
        request = {
            **self.request,
            "parameters": {
                "provider": {
                    "steps": [{"raw_hardware_command": "G28"}],
                }
            },
        }
        with self.assertRaisesRegex(InterfaceError, "raw-hardware"):
            self.gateway.submit(
                request,
                authenticated_identity="user:local",
                api_version="v1",
            )

    def test_unknown_request_fields_are_rejected(self):
        with self.assertRaisesRegex(InterfaceError, "unknown interface"):
            self.gateway.submit(
                {**self.request, "bypass_policy": True},
                authenticated_identity="user:local",
                api_version="v1",
            )

    def test_declared_and_negotiated_versions_must_match(self):
        with self.assertRaisesRegex(InterfaceError, "versions do not match"):
            self.gateway.submit(
                {**self.request, "api_version": "v9"},
                authenticated_identity="user:local",
                api_version="v1",
            )

    def test_request_identity_and_parameters_are_well_formed(self):
        with self.assertRaisesRegex(InterfaceError, "request_id"):
            self.gateway.submit(
                {**self.request, "request_id": " "},
                authenticated_identity="user:local",
                api_version="v1",
            )
        with self.assertRaisesRegex(InterfaceError, "parameters"):
            self.gateway.submit(
                {**self.request, "parameters": []},
                authenticated_identity="user:local",
                api_version="v1",
            )

    def test_local_identity_is_required(self):
        with self.assertRaises(InterfaceError):
            self.gateway.submit(
                self.request, authenticated_identity=None, api_version="v1"
            )

    def test_version_negotiation_is_explicit(self):
        self.assertEqual(self.gateway.negotiate(["v1"])["api_version"], "v1")
        self.assertFalse(self.gateway.negotiate(["v9"])["ok"])

    def test_action_explanation_is_complete_and_local_visible(self):
        result = self.gateway.action_summary(
            {
                "summary": "Start the approved Mission",
                "target": "mission:1",
                "reason": "The user requested it",
                "safety_conditions": ["verification passed"],
                "reversible": False,
                "failure_response": "Move to recovery",
                "approval_scope": "once",
                "data_behavior": "local_only",
            }
        )
        self.assertEqual(result["data_behavior"], "local_only")
        self.assertTrue(result["plain_language"])

    def test_standing_approval_has_visible_warning(self):
        result = self.gateway.approval_summary(
            {
                "requester": "user:local",
                "action": "mission.start",
                "scope": "printer:1",
                "expires_at": "2026-07-26T00:00:00Z",
                "targets": ["printer:1"],
                "risks": ["physical_motion"],
                "verification_state": "passed",
                "grant_type": "standing_policy",
                "revocation_method": "settings/approvals",
            }
        )
        self.assertTrue(result["standing_authority_warning"])

    def test_accessible_content_never_uses_color_alone(self):
        result = self.gateway.content(
            kind="alert",
            text="Printer unavailable",
            accessible_label="Alert: printer unavailable",
            cue="warning-icon",
        )
        self.assertEqual(result["non_color_cue"], "warning-icon")
        contract = self.gateway.accessibility_contract(mode="accessible")
        self.assertTrue(contract["same_core_workflows"])
        self.assertFalse(contract["pointer_only_actions"])

    def test_disabled_suggestions_remain_quiet(self):
        self.assertIsNone(
            self.gateway.content(
                kind="suggestion",
                text="Try this",
                accessible_label="Suggestion",
                cue="suggestion-icon",
                suggestions_enabled=False,
            )
        )

    def test_live_updates_are_observational(self):
        result = self.gateway.subscribe(
            "client:local", ["health.changed"], authorized=True
        )
        self.assertTrue(result["observational_only"])
        self.assertFalse(result["grants_control_authority"])

    def test_structured_error_explains_next_step(self):
        result = self.gateway.error(
            reason="capability_missing",
            summary="Calibration is unavailable.",
            affected_object="printer:1",
            next_step="Add a compatible sensor.",
        )
        self.assertEqual(
            result["error"]["recommended_next_step"], "Add a compatible sensor."
        )

    def test_schema_and_example_validate(self):
        from jsonschema import Draft202012Validator, ValidationError

        schema = json.loads(
            (ROOT / "schemas/fas/interface-request.schema.json").read_text()
        )
        example = json.loads(
            (ROOT / "examples/fas/interface-request.example.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        validator.validate(example)

        nested_raw_command = {
            **example,
            "parameters": {
                "provider": {
                    "steps": [{"raw_hardware_command": "G28"}],
                }
            },
        }
        with self.assertRaises(ValidationError):
            validator.validate(nested_raw_command)


if __name__ == "__main__":
    unittest.main()
