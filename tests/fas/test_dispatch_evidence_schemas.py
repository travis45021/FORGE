"""Schema tests for live-printer and final-provider evidence contracts."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from forge.fas.job_lifecycle import (
    final_confirmation_evidence,
    final_confirmation_evidence_digest,
)
from forge.fas.live_printer_checks import (
    REQUIRED_CHECKS,
    LivePrinterCheckService,
    live_check_evidence_digest,
)
from forge.fas.provider_dispatch import (
    ProviderDispatchCheckService,
    provider_dispatch_evidence_digest,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "examples" / "fas"


def schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / "fas" / name).read_text(encoding="utf-8"))


def example(name: str) -> dict:
    return json.loads((EXAMPLE_DIR / name).read_text(encoding="utf-8"))


def live_evidence() -> dict:
    return LivePrinterCheckService().evaluate(
        provider_id="provider:custom",
        artifact_digest="a" * 64,
        checks={name: True for name in REQUIRED_CHECKS},
        checked_at="2026-07-25T20:56:00Z",
        expires_at="2026-07-25T21:01:00Z",
    )


def provider_evidence() -> dict:
    return ProviderDispatchCheckService().evaluate(
        provider_id="provider:custom",
        context_id="context:print",
        capability_id="artifact.upload",
        checked_at="2026-07-25T20:59:50Z",
        expires_at="2026-07-25T21:00:20Z",
        checks={
            "provider_healthy": True,
            "current_state_allows": True,
            "capability_available": True,
        },
    )


def confirmation_evidence() -> dict:
    job = {
        "job_id": "job:print",
        "provider_id": "provider:custom",
        "artifact_digest": "a" * 64,
        "input_digest": "b" * 64,
        "profile_digest": "c" * 64,
        "engine_source_digest": "d" * 64,
        "engine_build_digest": "e" * 64,
        "comparison_id": "comparison:print",
        "comparison_evidence_digest": "f" * 64,
        "comparison_reviewed_by": "reviewer-1",
        "comparison_reviewed_at": "2026-07-25T20:50:00Z",
        "live_checks_checked_at": "2026-07-25T20:56:00Z",
        "live_checks_expires_at": "2026-07-25T21:01:00Z",
        "live_checks_evidence_digest": "9" * 64,
        "final_confirmed_by": "user-1",
        "final_confirmed_at": "2026-07-25T20:57:00Z",
        "confirmation_expires_at": "2026-07-25T21:05:00Z",
        "confirmation_token": "confirmation-" + ("x" * 32),
    }
    return {
        "evidence": final_confirmation_evidence(job),
        "evidence_digest": final_confirmation_evidence_digest(job),
    }


@pytest.mark.parametrize(
    ("schema_name", "factory"),
    [
        ("live-printer-check-evidence.schema.json", live_evidence),
        ("provider-dispatch-evidence.schema.json", provider_evidence),
        ("final-confirmation-evidence.schema.json", confirmation_evidence),
    ],
)
def test_generated_evidence_matches_schema(schema_name: str, factory) -> None:
    contract = schema(schema_name)
    Draft202012Validator.check_schema(contract)
    Draft202012Validator(contract).validate(factory())


@pytest.mark.parametrize(
    ("schema_name", "factory"),
    [
        ("live-printer-check-evidence.schema.json", live_evidence),
        ("provider-dispatch-evidence.schema.json", provider_evidence),
    ],
)
def test_schema_rejects_physical_authority(schema_name: str, factory) -> None:
    evidence = factory()
    evidence["can_upload"] = True

    with pytest.raises(ValidationError):
        Draft202012Validator(schema(schema_name)).validate(evidence)


@pytest.mark.parametrize(
    ("schema_name", "example_name"),
    [
        (
            "live-printer-check-evidence.schema.json",
            "live-printer-check-evidence.example.json",
        ),
        (
            "provider-dispatch-evidence.schema.json",
            "provider-dispatch-evidence.example.json",
        ),
        (
            "final-confirmation-evidence.schema.json",
            "final-confirmation-evidence.example.json",
        ),
    ],
)
def test_published_examples_match_schema(schema_name: str, example_name: str) -> None:
    Draft202012Validator(schema(schema_name)).validate(example(example_name))


@pytest.mark.parametrize(
    ("example_name", "digest"),
    [
        ("live-printer-check-evidence.example.json", live_check_evidence_digest),
        (
            "provider-dispatch-evidence.example.json",
            provider_dispatch_evidence_digest,
        ),
    ],
)
def test_published_evidence_digest_is_valid(example_name: str, digest) -> None:
    value = example(example_name)
    assert value["evidence_digest"] == digest(value)


def test_published_confirmation_digest_is_valid() -> None:
    value = example("final-confirmation-evidence.example.json")
    assert value["evidence_digest"] == final_confirmation_evidence_digest(
        value["evidence"]
    )


@pytest.mark.parametrize(
    "field",
    [
        "comparison_reviewed_at",
        "live_checks_checked_at",
        "live_checks_expires_at",
        "final_confirmed_at",
        "confirmation_expires_at",
    ],
)
def test_confirmation_schema_requires_utc_z_timestamps(field: str) -> None:
    value = confirmation_evidence()
    value["evidence"][field] = "2026-07-25T16:00:00-05:00"

    with pytest.raises(ValidationError):
        Draft202012Validator(
            schema("final-confirmation-evidence.schema.json")
        ).validate(value)
