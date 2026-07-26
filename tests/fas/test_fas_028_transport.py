import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.transport import HardwareTransportRegistry, TransportError


class Fas028TransportTests(unittest.TestCase):
    def setUp(self):
        self.registry = HardwareTransportRegistry()
        self.provider = {
            "provider_id": "provider:custom-printer",
            "transport": "local-moonraker",
            "capabilities": ["motion", "thermal"],
            "state": "registered",
            "health": "healthy",
        }
        self.registry.register(self.provider)

    def command(self):
        return {
            "command_id": "command:001",
            "capability_id": "motion",
            "operation": "move",
            "parameters": {"x": 1},
            "expires_at": "2026-07-26T12:01:00Z",
        }

    def test_provider_discovery_is_capability_first(self):
        self.assertEqual(
            ["motion", "thermal"], self.registry.discover()[0]["capabilities"]
        )

    def test_preparation_requires_every_gate_and_has_no_physical_side_effect(self):
        with self.assertRaises(TransportError):
            self.registry.prepare_command(
                "provider:custom-printer",
                self.command(),
                authorization_verified=True,
                verification_passed=True,
                runtime_lease_active=True,
                user_confirmation=False,
            )
        result = self.registry.prepare_command(
            "provider:custom-printer",
            self.command(),
            authorization_verified=True,
            verification_passed=True,
            runtime_lease_active=True,
            user_confirmation=True,
        )
        self.assertFalse(result["physical_dispatch_allowed"])
        self.assertTrue(result["requires_fresh_user_confirmation"])

    def test_raw_commands_and_unhealthy_providers_are_rejected(self):
        raw = {**self.command(), "raw_hardware_command": "G1 X1"}
        with self.assertRaises(TransportError):
            self.registry.prepare_command(
                "provider:custom-printer",
                raw,
                authorization_verified=True,
                verification_passed=True,
                runtime_lease_active=True,
                user_confirmation=True,
            )
        self.registry.set_health(
            "provider:custom-printer", "failed", observed_at="2026-07-26T12:00:00Z"
        )
        with self.assertRaises(TransportError):
            self.registry.prepare_command(
                "provider:custom-printer",
                self.command(),
                authorization_verified=True,
                verification_passed=True,
                runtime_lease_active=True,
                user_confirmation=True,
            )


if __name__ == "__main__":
    unittest.main()
