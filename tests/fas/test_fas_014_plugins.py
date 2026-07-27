"""Behavior and schema tests for canonical FAS-014."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.capabilities import CapabilityError
from forge.fas.plugins import (
    PluginError,
    PluginRegistry,
    custom_component_manifest,
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas014PluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_json(
            ROOT / "examples" / "fas" / "plugin-custom-filament-sensor.example.json"
        )
        self.registry = PluginRegistry()

    def ready(self, trust_state: str = "locally_trusted") -> dict:
        self.registry.discover(self.manifest)
        return self.registry.validate(
            self.manifest["plugin_id"],
            granted_permissions=self.manifest["permissions"],
            passed_contract_tests=self.manifest["validation_tests"],
            trust_state=trust_state,
        )

    def test_manifest_validation_does_not_grant_trust(self) -> None:
        result = self.registry.discover(self.manifest)
        self.assertEqual("manifest_validated", result["state"])
        self.assertEqual("unverified", result["trust_state"])
        self.assertEqual([], result["granted_permissions"])

    def test_undeclared_permission_is_rejected(self) -> None:
        self.registry.discover(self.manifest)
        with self.assertRaisesRegex(PluginError, "undeclared"):
            self.registry.validate(
                self.manifest["plugin_id"],
                granted_permissions=["network.internet"],
                passed_contract_tests=self.manifest["validation_tests"],
            )

    def test_missing_permission_or_contract_test_prevents_readiness(self) -> None:
        self.registry.discover(self.manifest)
        result = self.registry.validate(
            self.manifest["plugin_id"],
            granted_permissions=[],
            passed_contract_tests=self.manifest["validation_tests"],
        )
        self.assertEqual("configured", result["state"])
        result = self.registry.validate(
            self.manifest["plugin_id"],
            granted_permissions=self.manifest["permissions"],
            passed_contract_tests=["manifest"],
        )
        self.assertEqual("validation_failed", result["state"])

    def test_activation_requires_executive_authority(self) -> None:
        self.ready()
        with self.assertRaisesRegex(PluginError, "Executive authorization"):
            self.registry.activate(
                self.manifest["plugin_id"], executive_authorized=False
            )

    def test_active_plugin_registers_only_declared_capability(self) -> None:
        self.ready()
        self.registry.activate(self.manifest["plugin_id"], executive_authorized=True)
        contract = self.registry.capabilities().resolve(
            {
                "capability_id": "filament.runout_detection",
                "version_constraint": "^1.0.0",
                "operations": ["read_state"],
            }
        )
        self.assertEqual(self.manifest["plugin_id"], contract["plugin_id"])
        self.assertEqual(["requires_manual_test"], contract["limitations"])

    def test_provisional_provider_does_not_resolve_as_trusted(self) -> None:
        self.ready(trust_state="provisional")
        self.registry.activate(self.manifest["plugin_id"], executive_authorized=True)
        with self.assertRaises(CapabilityError):
            self.registry.capabilities().resolve(
                {
                    "capability_id": "filament.runout_detection",
                    "version_constraint": "^1.0.0",
                    "operations": ["read_state"],
                }
            )

    def test_internet_scope_requires_explicit_permission(self) -> None:
        changed = {**self.manifest, "network_scope": "internet"}
        with self.assertRaisesRegex(PluginError, "internet scope"):
            self.registry.discover(changed)

    def test_custom_component_builder_is_least_privilege(self) -> None:
        manifest = custom_component_manifest(
            plugin_id="local.custom.extruder",
            name="Garage Extruder",
            category="extrusion",
            capability_id="material.extrusion",
            operations=["extrude"],
            limits={"max_temperature_c": 285},
            connection={"type": "moonraker", "endpoint": "local"},
        )
        self.assertEqual(["machine.extrusion.control"], manifest["permissions"])
        self.assertTrue(manifest["experimental"])
        self.assertEqual("test_hardware", manifest["execution_mode"])

    def test_quarantine_is_narrow_and_explained(self) -> None:
        self.ready()
        result = self.registry.quarantine(
            self.manifest["plugin_id"], reason="Contract health check failed"
        )
        self.assertEqual("quarantined", result["state"])
        self.assertIn("health check", result["explanation"])

    def test_official_namespace_impersonation_is_rejected(self) -> None:
        changed = deepcopy(self.manifest)
        changed["plugin_id"] = "forge.official.fake"
        with self.assertRaisesRegex(PluginError, "official namespace"):
            self.registry.discover(changed)

    def test_schema_and_example_validate(self) -> None:
        from jsonschema import Draft202012Validator

        schema = load_json(ROOT / "schemas" / "fas" / "plugin-manifest.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.manifest)


if __name__ == "__main__":
    unittest.main()
