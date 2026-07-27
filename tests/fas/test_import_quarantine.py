"""Security tests for local STEP/3MF quarantine assessment."""

import sys
import tempfile
import unittest
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
            path.write_text("ISO-10303-21;\nHEADER;\nENDSEC;", encoding="ascii")
            result = self.quarantine.assess(path)
        self.assertEqual(result["decision"], "accepted")
        self.assertFalse(result["can_authorize_production"])

    def test_accepts_standard_3mf_member(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "part.3mf"
            with ZipFile(path, "w") as archive:
                archive.writestr("3D/3dmodel.model", "<model />")
            result = self.quarantine.assess(path)
        self.assertEqual(result["decision"], "accepted")
        self.assertTrue(result["quarantine"]["path_traversal_checked"])

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
