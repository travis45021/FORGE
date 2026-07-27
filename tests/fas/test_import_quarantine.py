"""Security tests for local STEP/3MF quarantine assessment."""

import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.imports import ImportAssessmentError, ImportQuarantine


class ImportQuarantineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quarantine = ImportQuarantine()

    def test_accepts_structured_step(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "part.step"
            path.write_text(
                "ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n",
                encoding="ascii",
            )
            result = self.quarantine.assess(path)
        self.assertEqual(result["decision"], "accepted")
        self.assertEqual(len(result["normalized_digest"]), 64)
        self.assertFalse(result["can_authorize_production"])

    def test_accepts_standard_3mf_member(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "part.3mf"
            with ZipFile(path, "w") as archive:
                archive.writestr(
                    "3D/3dmodel.model",
                    "<model><resources/><build/></model>",
                )
            result = self.quarantine.assess(path)
        self.assertEqual(result["decision"], "accepted")
        self.assertEqual(len(result["normalized_digest"]), 64)
        self.assertTrue(result["quarantine"]["path_traversal_checked"])

    def test_step_normalization_ignores_line_endings_and_trailing_space(self) -> None:
        content = "ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n"
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.step"
            second = Path(directory) / "second.stp"
            first.write_text(content, encoding="ascii", newline="\n")
            second.write_text(
                content.replace("\n", "  \r\n"),
                encoding="ascii",
                newline="",
            )
            first_result = self.quarantine.assess(first)
            second_result = self.quarantine.assess(second)
        self.assertEqual(
            first_result["normalized_digest"],
            second_result["normalized_digest"],
        )

    def test_rejects_malformed_3mf_model_xml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.3mf"
            with ZipFile(path, "w") as archive:
                archive.writestr("3D/3dmodel.model", "<model>")
            with self.assertRaises(ImportAssessmentError):
                self.quarantine.assess(path)

    def test_rejects_duplicate_3mf_members(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.3mf"
            with ZipFile(path, "w") as archive:
                archive.writestr("3D/3dmodel.model", "<model />")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr("3D/3dmodel.model", "<model />")
            with self.assertRaises(ImportAssessmentError):
                self.quarantine.assess(path)

    def test_rejects_3mf_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hostile.3mf"
            with ZipFile(path, "w") as archive:
                archive.writestr("../outside.txt", "unsafe")
            with self.assertRaises(ImportAssessmentError):
                self.quarantine.assess(path)

    def test_rejects_unsupported_f3d(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "part.f3d"
            path.write_bytes(b"not supported")
            with self.assertRaises(ImportAssessmentError):
                self.quarantine.assess(path)


if __name__ == "__main__":
    unittest.main()
