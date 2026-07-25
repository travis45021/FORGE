"""Behavior and schema tests for reconstructed FAS-001 through FAS-006."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.capabilities import CapabilityError, CapabilityRegistry
from forge.fas.events import EventError, IdempotentConsumer, validate_event
from forge.fas.executive import ExecutiveError, ForgeExecutive
from forge.fas.missions import MissionLifecycle, MissionTransitionError


def load(name):
    with (ROOT / "examples" / "fas" / name).open(encoding="utf-8") as stream:
        return json.load(stream)


class ReconstructionBehaviorTests(unittest.TestCase):
    def test_unknown_hardware_capability_registers_and_resolves(self):
        registry = CapabilityRegistry()
        contract = load("capability-user-heater.example.json")
        registry.register(contract)
        result = registry.resolve({
            "capability_id": "user.thermal.zone",
            "version_constraint": "^1.0.0",
            "operations": ["user.thermal.set_target"],
        })
        self.assertEqual("user-device:custom-heater-01", result["provider_id"])

    def test_unhealthy_capability_fails_resolution(self):
        registry = CapabilityRegistry()
        registry.register(load("capability-user-heater.example.json"), healthy=False)
        with self.assertRaises(CapabilityError):
            registry.resolve({
                "capability_id": "user.thermal.zone",
                "version_constraint": "^1.0.0",
                "operations": ["user.thermal.set_target"],
            })

    def test_mission_lifecycle_accepts_valid_transition(self):
        mission = load("mission-print.example.json")
        updated, event = MissionLifecycle().transition(
            mission, "validated", actor_id="forge-service:validator",
            reason="contract valid", event_id="forge-event:transition-1",
        )
        self.assertEqual("validated", updated["state"])
        self.assertEqual(2, updated["revision"])
        self.assertEqual("created", event["payload"]["from"])

    def test_mission_cannot_skip_approval_path(self):
        with self.assertRaises(MissionTransitionError):
            MissionLifecycle().transition(
                load("mission-print.example.json"), "executing",
                actor_id="forge-user:owner", reason="skip",
                event_id="forge-event:transition-2",
            )

    def test_event_duplicate_is_idempotent(self):
        event = load("event-mission-created.example.json")
        consumer = IdempotentConsumer()
        self.assertTrue(consumer.accept(event))
        self.assertFalse(consumer.accept(event))

    def test_event_partition_order_is_enforced(self):
        event = load("event-mission-created.example.json")
        consumer = IdempotentConsumer()
        consumer.accept(event)
        second = deepcopy(event)
        second["event_id"] = "forge-event:second"
        with self.assertRaises(EventError):
            consumer.accept(second)

    def test_event_classifications_are_distinct(self):
        event = load("event-mission-created.example.json")
        for classification in ("event", "request", "command", "decision", "evidence", "state"):
            candidate = deepcopy(event)
            candidate["classification"] = classification
            self.assertEqual(classification, validate_event(candidate)["classification"])

    def test_executive_requires_approved_mission_and_allow(self):
        mission = load("mission-print.example.json")
        contract = load("capability-user-heater.example.json")
        authorization = {
            "outcome": "allow",
            "evaluation_id": "forge-authorization:test",
            "decision_id": "forge-decision:test",
            "effective_action": {"action_type": "forge.print.start", "target_refs": ["forge-printer:test"], "parameters": {}},
        }
        with self.assertRaises(ExecutiveError):
            ForgeExecutive().prepare_execution(mission, authorization, contract)
        mission["state"] = "approved"
        result = ForgeExecutive().prepare_execution(mission, authorization, contract)
        self.assertEqual("command", result["classification"])
        authorization["outcome"] = "challenge"
        with self.assertRaises(ExecutiveError):
            ForgeExecutive().prepare_execution(mission, authorization, contract)


@unittest.skipUnless(__import__("importlib").util.find_spec("jsonschema"), "jsonschema not installed")
class ReconstructionSchemaTests(unittest.TestCase):
    def test_examples_validate(self):
        from jsonschema import Draft202012Validator, FormatChecker
        pairs = {
            "kernel-service-manifest.schema.json": "kernel-service-custom-printer.example.json",
            "capability-contract.schema.json": "capability-user-heater.example.json",
            "mission.schema.json": "mission-print.example.json",
            "event-envelope.schema.json": "event-mission-created.example.json",
        }
        for schema_name, example_name in pairs.items():
            with self.subTest(schema=schema_name):
                with (ROOT / "schemas" / "fas" / schema_name).open(encoding="utf-8") as stream:
                    schema = json.load(stream)
                Draft202012Validator(schema, format_checker=FormatChecker()).validate(load(example_name))
