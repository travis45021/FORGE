"""Tests for production/twin slicer worker isolation."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.slicer_worker import (
    REQUIRED_FORBIDDEN,
    SlicerWorkerBoundary,
    SlicerWorkerError,
)


def manifest(context: str, root: str) -> dict:
    return {
        "worker_id": f"worker-{context}",
        "context": context,
        "workspace": {
            "input": f"{root}/input",
            "output": f"{root}/output",
            "logs": f"{root}/logs",
        },
        "limits": {
            "timeout_seconds": 300,
            "memory_bytes": 1_000_000,
            "disk_bytes": 10_000_000,
        },
        "forbidden_capabilities": sorted(REQUIRED_FORBIDDEN),
    }


class SlicerWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = SlicerWorkerBoundary()

    def test_accepts_isolated_pair(self) -> None:
        production, twin = self.boundary.validate_pair(
            manifest("production", "work/production"),
            manifest("twin", "work/twin"),
        )
        self.assertFalse(production["can_control_hardware"])
        self.assertFalse(twin["can_control_hardware"])

    def test_rejects_each_missing_forbidden_capability(self) -> None:
        for capability in sorted(REQUIRED_FORBIDDEN):
            item = manifest("production", "work/production")
            item["forbidden_capabilities"].remove(capability)
            with (
                self.subTest(capability=capability),
                self.assertRaises(SlicerWorkerError),
            ):
                self.boundary.validate(item)

    def test_rejects_hardware_claim_unknown_fields_and_duplicate_forbidden(
        self,
    ) -> None:
        cases = (
            {"can_control_hardware": True},
            {"network_endpoint": "printer.local"},
            {
                "forbidden_capabilities": [
                    *sorted(REQUIRED_FORBIDDEN),
                    "printer_control",
                ]
            },
        )
        for changes in cases:
            item = manifest("production", "work/production")
            item.update(changes)
            with self.subTest(changes=changes), self.assertRaises(SlicerWorkerError):
                self.boundary.validate(item)

    def test_rejects_overlapping_pair(self) -> None:
        with self.assertRaises(SlicerWorkerError):
            self.boundary.validate_pair(
                manifest("production", "work/shared"),
                manifest("twin", "work/shared"),
            )

    def test_rejects_alias_overlap_and_nested_workspace_roots(self) -> None:
        alias = manifest("twin", "work/twin")
        alias["workspace"] = {
            "input": "work/production/../production/input",
            "output": "work/twin/output",
            "logs": "work/twin/logs",
        }
        with self.assertRaisesRegex(SlicerWorkerError, "canonical relative"):
            self.boundary.validate_pair(
                manifest("production", "work/production"),
                alias,
            )

        with self.assertRaisesRegex(SlicerWorkerError, "must not overlap"):
            self.boundary.validate_pair(
                manifest("production", "work/production"),
                manifest("twin", "work/production/twin"),
            )

    def test_rejects_absolute_or_mixed_workspace_paths(self) -> None:
        for unsafe in (
            "/tmp/forge/input",
            "C:/forge/input",
            r"work\production\input",
        ):
            item = manifest("production", "work/production")
            item["workspace"]["input"] = unsafe
            with (
                self.subTest(unsafe=unsafe),
                self.assertRaisesRegex(SlicerWorkerError, "relative POSIX"),
            ):
                self.boundary.validate(item)


if __name__ == "__main__":
    unittest.main()
