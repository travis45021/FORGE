"""Schema validation tests for FAS-008 examples."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

try:
    import jsonschema
except ImportError:  # pragma: no cover - environment-dependent test skip
    jsonschema = None


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.authorization import AuthorizationEngine  # noqa: E402


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


@unittest.skipIf(jsonschema is None, "jsonschema package is not installed")
class Fas008SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema_dir = ROOT / "schemas" / "fas"
        example_dir = ROOT / "examples" / "fas"
        cls.policy_schema = load_json(schema_dir / "policy.schema.json")
        cls.request_schema = load_json(
            schema_dir / "authorization-request.schema.json"
        )
        cls.result_schema = load_json(
            schema_dir / "authorization-result.schema.json"
        )
        cls.policy = load_json(
            example_dir / "policy-print-start.example.json"
        )
        cls.request = load_json(
            example_dir / "authorization-request-print-start.example.json"
        )

    def validate(self, instance: dict, schema: dict) -> None:
        jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        ).validate(instance)

    def test_policy_example_is_valid(self) -> None:
        self.validate(self.policy, self.policy_schema)

    def test_request_example_is_valid(self) -> None:
        self.validate(self.request, self.request_schema)

    def test_evaluator_result_is_valid(self) -> None:
        result = AuthorizationEngine().evaluate(self.request, [self.policy])
        self.validate(result, self.result_schema)

    def test_unknown_action_pattern_is_valid(self) -> None:
        policy = deepcopy(self.policy)
        policy["action_patterns"] = ["user-hardware.*"]
        self.validate(policy, self.policy_schema)

    def test_invalid_readiness_level_is_rejected(self) -> None:
        request = deepcopy(self.request)
        request["readiness_level"] = 6
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(request, self.request_schema)


if __name__ == "__main__":
    unittest.main()

