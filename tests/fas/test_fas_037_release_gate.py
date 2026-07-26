import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.release_gate import REQUIRED_GATES, ReleaseGate, ReleaseGateError


class Fas037ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = ReleaseGate()
        self.evidence = {name: True for name in REQUIRED_GATES}

    def test_complete_evidence_is_ready_for_human_decision_only(self):
        result = self.gate.evaluate(
            self.evidence,
            reviewed_by="forge-user:release",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("ready_for_final_human_decision", result["status"])
        self.assertFalse(result["release_authorized"])

    def test_failed_gate_blocks_release(self):
        self.evidence["licensing"] = False
        result = self.gate.evaluate(
            self.evidence,
            reviewed_by="forge-user:release",
            reviewed_at="2026-07-26T12:00:00Z",
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual(["licensing"], result["failed_gates"])

    def test_missing_gate_rejected(self):
        self.evidence.pop("security")
        with self.assertRaises(ReleaseGateError):
            self.gate.evaluate(
                self.evidence,
                reviewed_by="forge-user:release",
                reviewed_at="2026-07-26T12:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
