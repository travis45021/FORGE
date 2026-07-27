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
        self.profile = {
            "profile_digest": "d" * 64,
            "content": {"machine": {"capabilities": ["fff.extrusion"]}},
            "lifecycle": "ephemeral",
            "persist_after_worker": False,
            "delete_after_result": True,
            "hardware_neutral": True,
            "contains_transport_endpoint": False,
            "contains_credentials": False,
            "cloud_access": False,
            "can_control_printer": False,
            "can_upload": False,
            "can_start_print": False,
        }

    def prepare(self) -> dict:
        return self.service.prepare(
            request_id="request-1",
            mission_id="mission-1",
            source_path="quarantine/part.3mf",
            context="production",
            assessment=self.assessment,
            intent=self.intent,
            derived_profile=self.profile,
        )

    def test_prepares_request_from_matching_evidence(self) -> None:
        request = self.prepare()
        self.assertEqual(request["profile_digest"], "d" * 64)
        self.assertTrue(request["profile_ephemeral"])
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

    def test_rejects_profile_with_printer_authority(self) -> None:
        self.profile["can_control_printer"] = True
        with self.assertRaises(SlicerPreparationError):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
