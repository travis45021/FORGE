"""Hostile STEP fixture tests for pre-slicer quarantine."""

from pathlib import Path

import pytest

from forge.fas.imports import ImportAssessmentError, ImportQuarantine

HEADER = b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\n"


def test_rejects_binary_nul_data(tmp_path: Path) -> None:
    path = tmp_path / "binary.step"
    path.write_bytes(HEADER + b"#1=POINT(\x00);\nENDSEC;\nEND-ISO-10303-21;\n")

    with pytest.raises(ImportAssessmentError, match="binary NUL"):
        ImportQuarantine().assess(path)


def test_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "invalid-text.step"
    path.write_bytes(HEADER + b"\xff\xfe\nENDSEC;\nEND-ISO-10303-21;\n")

    with pytest.raises(ImportAssessmentError, match="UTF-8"):
        ImportQuarantine().assess(path)


def test_rejects_pathological_line_length(tmp_path: Path) -> None:
    path = tmp_path / "long-line.step"
    path.write_bytes(
        HEADER
        + (b"A" * (ImportQuarantine.MAX_STEP_LINE_BYTES + 1))
        + b"\nENDSEC;\nEND-ISO-10303-21;\n"
    )

    with pytest.raises(ImportAssessmentError, match="oversized line"):
        ImportQuarantine().assess(path)


def test_rejects_oversized_step_before_reading(tmp_path: Path) -> None:
    path = tmp_path / "oversized.step"
    with path.open("wb") as stream:
        stream.write(HEADER)
        stream.truncate(ImportQuarantine.MAX_STEP_BYTES + 1)

    with pytest.raises(ImportAssessmentError, match="size limit"):
        ImportQuarantine().assess(path)
