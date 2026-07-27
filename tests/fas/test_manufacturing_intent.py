"""Tests for user-confirmed Manufacturing Intent."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.manufacturing_intent import (
    ManufacturingIntentError,
    ManufacturingIntentService,
)


class ManufacturingIntentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ManufacturingIntentService()
        self.intent = {
            "intent_id": "intent-1",
            "source_digest": "a" * 64,
            "printer_capabilities": ["fff.extrusion", "heated_bed"],
            "material": {"name": "PLA"},
            "process": {"profile_digest": "b" * 64},
            "user_decisions": {
                "context_confirmed": True,
                "mission_reviewed": True,
            },
        }

    def test_validates_confirmed_intent(self) -> None:
        result = self.service.validate(self.intent)
        self.assertFalse(result["can_authorize_production"])

    def test_rejects_missing_capabilities(self) -> None:
        self.intent["printer_capabilities"] = []
        with self.assertRaises(ManufacturingIntentError):
            self.service.validate(self.intent)

    def test_rejects_unreviewed_mission(self) -> None:
        self.intent["user_decisions"]["mission_reviewed"] = False
        with self.assertRaises(ManufacturingIntentError):
            self.service.validate(self.intent)


if __name__ == "__main__":
    unittest.main()
