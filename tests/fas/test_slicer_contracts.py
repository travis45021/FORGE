"""Validation coverage for the contract-only Gate 3 slicer schemas."""

import json
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, ValidationError
except ImportError:  # pragma: no cover - optional validation dependency
    Draft202012Validator = None
    ValidationError = Exception


ROOT = Path(__file__).parents[2]
SCHEMA_DIR = ROOT / "schemas" / "fas"


@unittest.skipIf(Draft202012Validator is None, "jsonschema package is not installed")
class SlicerContractTests(unittest.TestCase):
    def load(self, name: str) -> dict:
        return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))

    def test_schemas_are_valid(self) -> None:
        for name in (
            "import-assessment.schema.json",
            "manufacturing-intent.schema.json",
            "slicer-request.schema.json",
            "slicer-result.schema.json",
        ):
            Draft202012Validator.check_schema(self.load(name))

    def test_result_cannot_grant_physical_authority(self) -> None:
        schema = self.load("slicer-result.schema.json")
        result = {
            "contract_version": "1.0",
            "request_id": "req-1",
            "status": "succeeded",
            "context": "twin",
            "engine": {
                "name": "contract-test",
                "version": "0",
                "source_digest": "a" * 64,
                "build_digest": "b" * 64,
            },
            "warnings": [],
            "authority": {"can_upload": False, "can_start_print": False},
        }
        Draft202012Validator(schema).validate(result)
        result["authority"]["can_start_print"] = True
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(result)


if __name__ == "__main__":
    unittest.main()
