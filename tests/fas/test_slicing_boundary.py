"""Behavior tests for the FORGE-side slicer contract boundary."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.slicing import SlicerContractBoundary, SlicerContractError


class SlicerBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = SlicerContractBoundary()

    def test_accepts_supported_request(self) -> None:
        request = self.boundary.request(
            {
                "request_id": "req-1",
                "input": {"format": "3mf", "digest": "a" * 64, "path": "in/part.3mf"},
                "context": "twin",
                "profile_digest": "b" * 64,
                "authority": {
                    "mission_id": "mission-1",
                    "user_confirmation_stage": "created_mission",
                },
            }
        )
        self.assertEqual(request["context"], "twin")

    def test_rejects_unsupported_format(self) -> None:
        with self.assertRaises(SlicerContractError):
            self.boundary.request(
                {
                    "request_id": "req-1",
                    "input": {"format": "f3d", "digest": "a" * 64, "path": "part.f3d"},
                    "context": "production",
                    "profile_digest": "b" * 64,
                    "authority": {
                        "mission_id": "mission-1",
                        "user_confirmation_stage": "created_mission",
                    },
                }
            )

    def test_rejects_result_that_grants_print_authority(self) -> None:
        with self.assertRaises(SlicerContractError):
            self.boundary.result(
                {
                    "request_id": "req-1",
                    "status": "succeeded",
                    "context": "production",
                    "engine": {
                        "name": "test",
                        "version": "0",
                        "source_digest": "c" * 64,
                    },
                    "warnings": [],
                    "authority": {"can_upload": False, "can_start_print": True},
                }
            )


if __name__ == "__main__":
    unittest.main()
