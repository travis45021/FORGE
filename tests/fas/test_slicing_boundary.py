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
                "contract_version": "1.0",
                "request_id": "req-1",
                "input": {"format": "3mf", "digest": "a" * 64, "path": "in/part.3mf"},
                "context": "twin",
                "profile_digest": "b" * 64,
                "profile_ephemeral": True,
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
                    "contract_version": "1.0",
                    "request_id": "req-1",
                    "input": {"format": "f3d", "digest": "a" * 64, "path": "part.f3d"},
                    "context": "production",
                    "profile_digest": "b" * 64,
                    "profile_ephemeral": True,
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
                    "contract_version": "1.0",
                    "request_id": "req-1",
                    "status": "succeeded",
                    "context": "production",
                    "engine": {
                        "name": "test",
                        "version": "0",
                        "source_digest": "c" * 64,
                        "build_digest": "d" * 64,
                    },
                    "artifact_digest": "a" * 64,
                    "warnings": [],
                    "authority": {"can_upload": False, "can_start_print": True},
                }
            )

    def test_rejects_result_without_exact_engine_build(self) -> None:
        with self.assertRaisesRegex(SlicerContractError, "build_digest"):
            self.boundary.result(
                {
                    "contract_version": "1.0",
                    "request_id": "req-1",
                    "status": "succeeded",
                    "context": "production",
                    "engine": {
                        "name": "test",
                        "version": "0",
                        "source_digest": "c" * 64,
                    },
                    "artifact_digest": "a" * 64,
                    "warnings": [],
                    "authority": {"can_upload": False, "can_start_print": False},
                }
            )

    def test_success_requires_artifact_and_failure_cannot_claim_one(self) -> None:
        base = {
            "contract_version": "1.0",
            "request_id": "req-1",
            "status": "succeeded",
            "context": "production",
            "engine": {
                "name": "test",
                "version": "0",
                "source_digest": "c" * 64,
                "build_digest": "d" * 64,
            },
            "warnings": [],
            "authority": {"can_upload": False, "can_start_print": False},
        }
        with self.assertRaisesRegex(SlicerContractError, "artifact digest"):
            self.boundary.result(base)

        base["status"] = "failed"
        base["artifact_digest"] = "a" * 64
        with self.assertRaisesRegex(SlicerContractError, "cannot claim"):
            self.boundary.result(base)


if __name__ == "__main__":
    unittest.main()
