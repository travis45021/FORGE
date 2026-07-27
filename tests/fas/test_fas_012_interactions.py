"""Behavior and schema tests for canonical FAS-012 interactions."""

from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.interactions import InteractionError, InteractionManager


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas012InteractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.suggestion = load_json(
            ROOT / "examples" / "fas" / "suggestion-calibration.example.json"
        )

    def manager(self, **changes: object) -> InteractionManager:
        preferences = {
            "interaction_profile": "guided",
            "ai_enabled": False,
            "suggestions_enabled": True,
            "automation_profile": "manual",
            "maximum_suggestions_per_day": 2,
            "maximum_suggestions_per_mission": 1,
            **changes,
        }
        return InteractionManager(preferences)

    def evaluate(
        self,
        manager: InteractionManager,
        suggestion: dict | None = None,
        **changes: object,
    ) -> dict:
        return manager.evaluate_suggestion(
            suggestion or self.suggestion,
            evaluated_at="2026-07-25T20:00:00Z",
            **changes,
        )

    def test_simple_defaults_are_ai_and_suggestion_free(self) -> None:
        preferences = InteractionManager().preferences()
        self.assertEqual("simple", preferences["interaction_profile"])
        self.assertFalse(preferences["ai_enabled"])
        self.assertFalse(preferences["suggestions_enabled"])
        self.assertEqual("manual", preferences["automation_profile"])

    def test_suggestion_free_preserves_essential_interactions(self) -> None:
        manager = InteractionManager()
        self.assertEqual(
            "suppress",
            manager.classify_delivery(
                "suggestion", evaluated_at="2026-07-25T20:00:00Z"
            )["disposition"],
        )
        for interaction_class in (
            "approval_request",
            "warning",
            "critical_alert",
        ):
            with self.subTest(interaction_class=interaction_class):
                self.assertEqual(
                    "deliver",
                    manager.classify_delivery(
                        interaction_class,
                        evaluated_at="2026-07-25T20:00:00Z",
                    )["disposition"],
                )

    def test_interaction_preferences_cannot_expand_automation(self) -> None:
        manager = InteractionManager()
        with self.assertRaisesRegex(InteractionError, "automation authority"):
            manager.update_preferences({"automation_profile": "autonomous"})
        manager.update_preferences({"interaction_profile": "proactive"})
        self.assertEqual("manual", manager.preferences()["automation_profile"])

    def test_ai_suggestion_fails_closed_when_ai_disabled(self) -> None:
        suggestion = {**self.suggestion, "source_type": "ai"}
        result = self.evaluate(self.manager(), suggestion)
        self.assertEqual("ai_disabled", result["reason_code"])

    def test_daily_and_mission_budgets_are_enforced(self) -> None:
        manager = self.manager()
        self.assertEqual(
            "deliver",
            self.evaluate(manager, mission_id="forge-mission:one")["disposition"],
        )
        manager.resolve_suggestion(self.suggestion["deduplication_key"])
        second = {
            **self.suggestion,
            "suggestion_id": "forge-suggestion:calibration-002",
            "deduplication_key": "calibration:flow:garage-printer",
        }
        result = self.evaluate(manager, second, mission_id="forge-mission:one")
        self.assertEqual("suggestion_budget_exhausted", result["reason_code"])
        result = self.evaluate(manager, second, mission_id="forge-mission:two")
        self.assertEqual("deliver", result["disposition"])
        manager.resolve_suggestion(second["deduplication_key"])
        third = {
            **second,
            "suggestion_id": "forge-suggestion:calibration-003",
            "deduplication_key": "calibration:steps:garage-printer",
        }
        result = self.evaluate(manager, third, mission_id="forge-mission:three")
        self.assertEqual("suggestion_budget_exhausted", result["reason_code"])

    def test_requested_help_bypasses_proactive_budget_not_ai_gate(self) -> None:
        manager = InteractionManager()
        result = self.evaluate(manager, requested=True)
        self.assertEqual("deliver", result["disposition"])
        ai_suggestion = {**self.suggestion, "source_type": "ai"}
        result = self.evaluate(manager, ai_suggestion, requested=True)
        self.assertEqual("ai_disabled", result["reason_code"])

    def test_deduplication_and_permanent_dismissal(self) -> None:
        manager = self.manager()
        self.assertEqual("deliver", self.evaluate(manager)["disposition"])
        self.assertEqual(
            "duplicate_active_suggestion",
            self.evaluate(manager)["reason_code"],
        )
        manager.dismiss_suggestion(self.suggestion, mode="permanent")
        self.assertEqual(
            "permanently_dismissed",
            self.evaluate(manager)["reason_code"],
        )

    def test_materially_new_evidence_reopens_dismissed_suggestion(self) -> None:
        manager = self.manager()
        manager.dismiss_suggestion(self.suggestion, mode="permanent")
        changed = deepcopy(self.suggestion)
        changed["evidence_digest"] = "sha256:" + "b" * 64
        self.assertEqual("deliver", self.evaluate(manager, changed)["disposition"])

    def test_quiet_hours_defer_suggestions_but_not_critical_alerts(self) -> None:
        manager = self.manager(quiet_hours={"start": "19:00", "end": "08:00"})
        self.assertEqual("quiet_hours", self.evaluate(manager)["reason_code"])
        self.assertEqual(
            "deliver",
            manager.classify_delivery(
                "critical_alert", evaluated_at="2026-07-25T20:00:00Z"
            )["disposition"],
        )

    def test_reset_preserves_automation_profile(self) -> None:
        manager = InteractionManager({"automation_profile": "supervised"})
        result = manager.reset_preferences()
        self.assertEqual("simple", result["interaction_profile"])
        self.assertEqual("supervised", result["automation_profile"])

    def test_examples_and_schemas_validate(self) -> None:
        from jsonschema import Draft202012Validator

        pairs = (
            (
                "interaction-profile.schema.json",
                "interaction-profile-simple.example.json",
            ),
            ("suggestion.schema.json", "suggestion-calibration.example.json"),
        )
        for schema_name, example_name in pairs:
            with self.subTest(schema=schema_name):
                schema = load_json(ROOT / "schemas" / "fas" / schema_name)
                example = load_json(ROOT / "examples" / "fas" / example_name)
                Draft202012Validator.check_schema(schema)
                Draft202012Validator(schema).validate(example)


if __name__ == "__main__":
    unittest.main()
