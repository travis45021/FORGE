"""Behavior and schema tests for canonical FAS-020."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.onboarding import OnboardingError, OnboardingService  # noqa: E402


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas020OnboardingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = OnboardingService()
        self.local_id = "local-user:owner"
        self.service.create_local_profile(
            self.local_id, display_name="Workshop Owner"
        )

    def test_local_identity_requires_no_network_account(self) -> None:
        profile = self.service.export(self.local_id)
        self.assertIsNone(profile["network_identity"])
        self.assertFalse(profile["sharing_consent"])

    def test_v1_exposes_only_three_profiles(self) -> None:
        for profile in ("offline_manual", "simple_local", "custom_builder"):
            service = OnboardingService()
            local_id = f"local-user:{profile}"
            service.create_local_profile(local_id, display_name=profile)
            self.assertEqual(
                profile,
                service.select_experience(local_id, profile)["experience_profile"],
            )
        for profile in ("assisted", "supervised_automation", "autonomous_path"):
            with self.assertRaisesRegex(OnboardingError, "future-gated"):
                self.service.select_experience(self.local_id, profile)

    def test_custom_builder_is_ai_free_and_custom_first(self) -> None:
        record = self.service.select_experience(
            self.local_id, "custom_builder"
        )
        self.assertFalse(record["settings"]["ai_enabled"])
        self.assertFalse(record["settings"]["suggestions_enabled"])
        self.assertEqual("custom", record["settings"]["hardware_setup"])

    def test_experience_settings_cannot_expand_authority(self) -> None:
        self.service.select_experience(self.local_id, "simple_local")
        with self.assertRaisesRegex(OnboardingError, "explicit flow"):
            self.service.update_settings(
                self.local_id, {"automation_authority": "autonomous"}
            )
        self.assertEqual(
            "manual", self.service.export(self.local_id)["automation_authority"]
        )

    def test_operational_twin_can_be_enabled_without_ai(self) -> None:
        self.service.select_experience(self.local_id, "offline_manual")
        result = self.service.update_settings(
            self.local_id, {"operational_twin_enabled": True}
        )
        self.assertTrue(result["settings"]["operational_twin_enabled"])
        self.assertFalse(result["settings"]["ai_enabled"])
        self.assertEqual("offline", result["settings"]["network_mode"])

    def test_shared_services_require_consent_and_separate_identity(self) -> None:
        self.service.select_experience(self.local_id, "simple_local")
        with self.assertRaisesRegex(OnboardingError, "consent"):
            self.service.set_network_participation(
                self.local_id,
                network_mode="shared_services",
                sharing_consent=False,
            )
        result = self.service.set_network_participation(
            self.local_id,
            network_mode="shared_services",
            sharing_consent=True,
            network_identity="forge-network-user:owner",
        )
        self.assertEqual(
            "forge-network-user:owner", result["network_identity"]
        )

    def test_transparency_summary_states_effective_choices(self) -> None:
        self.service.select_experience(self.local_id, "custom_builder")
        summary = self.service.summary(self.local_id)
        self.assertEqual("off", summary["ai"])
        self.assertEqual("off", summary["suggestions"])
        self.assertEqual("manual", summary["automation"])
        self.assertEqual("custom", summary["hardware_setup"])

    def test_schema_and_example_validate(self) -> None:
        from jsonschema import Draft202012Validator
        schema = load_json(
            ROOT / "schemas" / "fas" / "onboarding-profile.schema.json"
        )
        example = load_json(
            ROOT / "examples" / "fas" /
            "onboarding-profile-custom-builder.example.json"
        )
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(example)


if __name__ == "__main__":
    unittest.main()
