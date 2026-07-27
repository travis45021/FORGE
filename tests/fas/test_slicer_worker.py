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

    def test_rejects_missing_forbidden_capability(self) -> None:
        item = manifest("production", "work/production")
        item["forbidden_capabilities"].remove("printer_control")
        with self.assertRaises(SlicerWorkerError):
            self.boundary.validate(item)

    def test_rejects_overlapping_pair(self) -> None:
        with self.assertRaises(SlicerWorkerError):
            self.boundary.validate_pair(
                manifest("production", "work/shared"),
                manifest("twin", "work/shared"),
            )


if __name__ == "__main__":
    unittest.main()
