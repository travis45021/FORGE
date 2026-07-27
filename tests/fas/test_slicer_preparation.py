"""Tests for governed slicer request preparation."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.slicer_preparation import (
    SlicerMissionPreparation,
    SlicerPreparationError,
)


class SlicerPreparationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SlicerMissionPreparation()
        self.assessment = {
            "format": "3mf",
            "source_digest": "a" * 64,
            "quarantine": {"isolated": True},
            "decision": "accepted",
            "can_authorize_production": False,
        }
        self.intent = {
            "intent_id": "intent-1",
            "source_digest": "a" * 64,
            "printer_capabilities": ["fff.extrusion"],
            "material": {"name": "PLA"},
            "process": {"profile_digest": "b" * 64},
            "user_decisions": {
                "context_confirmed": True,
                "mission_reviewed": True,
            },
        }

    def prepare(self) -> dict:
        return self.service.prepare(
            request_id="request-1",
            mission_id="mission-1",
            source_path="quarantine/part.3mf",
            context="production",
            assessment=self.assessment,
            intent=self.intent,
        )

    def test_prepares_request_from_matching_evidence(self) -> None:
        request = self.prepare()
        self.assertEqual(request["profile_digest"], "b" * 64)
        self.assertEqual(
            request["authority"]["user_confirmation_stage"], "created_mission"
        )

    def test_rejects_unresolved_import(self) -> None:
        self.assessment["decision"] = "needs_user_resolution"
        with self.assertRaises(SlicerPreparationError):
            self.prepare()

    def test_rejects_digest_mismatch(self) -> None:
        self.intent["source_digest"] = "c" * 64
        with self.assertRaises(SlicerPreparationError):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
