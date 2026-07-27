"""Repository-wide validation for every published FAS JSON contract."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas" / "fas"
EXAMPLE_ROOT = ROOT / "examples" / "fas"

EXAMPLE_SCHEMAS = {
    "authorization-request-print-start.example.json": "authorization-request.schema.json",
    "authorization-result-allow.example.json": "authorization-result.schema.json",
    "backup-manifest-local.example.json": "backup-manifest.schema.json",
    "capability-user-heater.example.json": "capability-contract.schema.json",
    "data-record-profile.example.json": "data-record.schema.json",
    "decision-approved.example.json": "decision-record.schema.json",
    "dispatch-status-presentation.example.json": "dispatch-status-presentation.schema.json",
    "event-mission-created.example.json": "event-envelope.schema.json",
    "evidence-bed-selection.example.json": "evidence-record.schema.json",
    "execution-context-print.example.json": "execution-context.schema.json",
    "final-confirmation-evidence.example.json": "final-confirmation-evidence.schema.json",
    "forge-object-custom-extruder.example.json": "forge-object.schema.json",
    "fourth-click-presentation-record.example.json": "fourth-click-presentation-record.schema.json",
    "health-report-provider.example.json": "health-report.schema.json",
    "interaction-profile-simple.example.json": "interaction-profile.schema.json",
    "interface-request.example.json": "interface-request.schema.json",
    "kernel-service-custom-printer.example.json": "kernel-service-manifest.schema.json",
    "knowledge-nozzle.example.json": "knowledge-object.schema.json",
    "live-printer-check-evidence.example.json": "live-printer-check-evidence.schema.json",
    "mission-print.example.json": "mission.schema.json",
    "onboarding-profile-custom-builder.example.json": "onboarding-profile.schema.json",
    "plugin-custom-filament-sensor.example.json": "plugin-manifest.schema.json",
    "policy-bundle-production.example.json": "policy-bundle.schema.json",
    "policy-print-start.example.json": "policy.schema.json",
    "provider-dispatch-evidence.example.json": "provider-dispatch-evidence.schema.json",
    "release-assurance.example.json": "release-assurance.schema.json",
    "restore-plan-safe.example.json": "restore-plan.schema.json",
    "scheduled-mission-print.example.json": "scheduled-mission.schema.json",
    "slicer-reproducibility-evidence.example.json": "slicer-reproducibility-evidence.schema.json",
    "suggestion-calibration.example.json": "suggestion.schema.json",
    "trust-key-release.example.json": "trust-key.schema.json",
    "v1-release-gate.example.json": "v1-release-gate.schema.json",
    "verification-packet-calibration.example.json": "verification-packet.schema.json",
}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), f"{path} must contain a JSON object"
    return value


def test_every_schema_is_valid_and_uniquely_identified() -> None:
    identifiers: dict[str, str] = {}
    schema_paths = sorted(SCHEMA_ROOT.glob("*.schema.json"))
    assert schema_paths

    for path in schema_paths:
        schema = load(path)
        Draft202012Validator.check_schema(schema)
        assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
        expected_id = f"https://forge.local/schemas/fas/{path.name}"
        assert schema.get("$id") == expected_id
        identifier = schema["$id"]
        assert identifier not in identifiers, (
            f"{path.name} duplicates the identifier used by {identifiers[identifier]}"
        )
        identifiers[identifier] = path.name


def test_every_published_example_is_cataloged_and_schema_valid() -> None:
    example_names = {path.name for path in EXAMPLE_ROOT.glob("*.example.json")}
    assert set(EXAMPLE_SCHEMAS) == example_names

    checker = FormatChecker()
    for example_name, schema_name in sorted(EXAMPLE_SCHEMAS.items()):
        schema_path = SCHEMA_ROOT / schema_name
        assert schema_path.is_file(), (
            f"{example_name} references missing schema {schema_name}"
        )
        Draft202012Validator(
            load(schema_path),
            format_checker=checker,
        ).validate(load(EXAMPLE_ROOT / example_name))
