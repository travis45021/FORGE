import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from forge.fas.configuration import ConfigurationError, ConfigurationManager


def profile(i, f, v, limit=300, source="local", status="validated"):
    return {
        "profile_id": i,
        "family": f,
        "version": "1.0.0",
        "values": {"temperature": v},
        "hard_limits": {"temperature": limit},
        "provenance": ["evidence:test"],
        "status": status,
        "source": source,
    }


class TestFas021(unittest.TestCase):
    def test_layering_and_limits(self):
        m = ConfigurationManager()
        [
            m.register(p)
            for p in [
                profile("p:safe", "safe_defaults", 200),
                profile("p:user", "user", 220),
            ]
        ]
        self.assertEqual(220, m.resolve(["p:user", "p:safe"])["values"]["temperature"])

    def test_cannot_weaken_limit(self):
        m = ConfigurationManager()
        m.register(profile("p:s", "safe_defaults", 200, 300))
        m.register(profile("p:u", "user", 200, 350))
        with self.assertRaises(ConfigurationError):
            m.resolve(["p:s", "p:u"])

    def test_material_change_gates(self):
        m = ConfigurationManager()
        m.register(profile("p:base", "safe_defaults", 200))
        r = {
            "change_id": "c:1",
            "base_profile_id": "p:base",
            "new_profile": profile("p:new", "user", 210),
            "material": True,
            "verified": False,
            "backup_id": None,
            "rollback_profile_id": "p:base",
            "authorized": True,
        }
        with self.assertRaises(ConfigurationError):
            m.apply_change(r)
        r.update(verified=True, backup_id="backup:1")
        self.assertEqual("p:new", m.apply_change(r)["profile_id"])

    def test_active_mission_protected(self):
        m = ConfigurationManager()
        m.register(profile("p:base", "safe_defaults", 200))
        r = {
            "change_id": "c:1",
            "base_profile_id": "p:base",
            "new_profile": profile("p:new", "user", 210),
            "material": True,
            "verified": True,
            "backup_id": "b:1",
            "rollback_profile_id": "p:base",
            "authorized": True,
        }
        with self.assertRaises(ConfigurationError):
            m.apply_change(r, active_mission=True)

    def test_ai_profile_provisional(self):
        m = ConfigurationManager()
        m.register(profile("p:base", "safe_defaults", 200))
        r = {
            "change_id": "c:1",
            "base_profile_id": "p:base",
            "new_profile": profile("p:ai", "user", 210, source="ai"),
            "material": False,
            "verified": True,
            "backup_id": None,
            "rollback_profile_id": "p:base",
            "authorized": True,
        }
        with self.assertRaises(ConfigurationError):
            m.apply_change(r)

    def test_rollback_authorized(self):
        m = ConfigurationManager()
        m.register(profile("p:base", "safe_defaults", 200))
        with self.assertRaises(ConfigurationError):
            m.rollback("p:base", authorized=False)
        self.assertEqual("p:base", m.rollback("p:base", authorized=True)["profile_id"])


if __name__ == "__main__":
    unittest.main()
