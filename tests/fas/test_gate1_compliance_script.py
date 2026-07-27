"""Tests for the fail-closed Gate 1 repository evidence check."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_current_gate1_evidence_passes_but_remains_blocked() -> None:
    path = ROOT / "scripts/check_gate1.py"
    spec = importlib.util.spec_from_file_location("check_gate1", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.main() == 0
