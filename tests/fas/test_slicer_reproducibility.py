"""Tests for repeated slicer-result reproducibility evidence."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from forge.fas.slicer_reproducibility import (
    SlicerReproducibilityError,
    SlicerReproducibilityService,
    reproducibility_evidence_digest,
)

ROOT = Path(__file__).resolve().parents[2]


def result(request_id: str, *, artifact: str = "a", warnings=None) -> dict:
    return {
        "contract_version": "1.0",
        "request_id": request_id,
        "status": "succeeded",
        "context": "production",
        "engine": {
            "name": "reviewed-engine",
            "version": "1.0",
            "source_digest": "c" * 64,
            "build_digest": "d" * 64,
        },
        "artifact_digest": artifact * 64,
        "warnings": [] if warnings is None else warnings,
        "authority": {"can_upload": False, "can_start_print": False},
    }


def evaluate(results: list[dict]) -> dict:
    return SlicerReproducibilityService().evaluate(
        run_group_id="reproducibility:1",
        input_digest="e" * 64,
        profile_digest="f" * 64,
        results=results,
    )


def test_matching_repeated_results_produce_non_authoritative_evidence() -> None:
    evidence = evaluate([result("request:1"), result("request:2")])

    assert evidence["reproducible"] is True
    assert evidence["reason"] == "repeated_results_match"
    assert evidence["run_count"] == 2
    assert evidence["real_engine_runs_required"] is True
    assert evidence["can_authorize_production"] is False
    assert evidence["can_upload"] is False
    assert evidence["evidence_digest"] == reproducibility_evidence_digest(evidence)


def test_artifact_mismatch_is_preserved_as_failed_evidence() -> None:
    evidence = evaluate([result("request:1"), result("request:2", artifact="b")])

    assert evidence["reproducible"] is False
    assert evidence["artifacts_match"] is False
    assert evidence["reason"] == "artifact_digest_mismatch"
    assert evidence["artifact_digests"] == ["a" * 64, "b" * 64]


def test_warning_mismatch_is_visible() -> None:
    evidence = evaluate(
        [result("request:1"), result("request:2", warnings=["changed warning"])]
    )

    assert evidence["reproducible"] is False
    assert evidence["artifacts_match"] is True
    assert evidence["warnings_match"] is False
    assert evidence["reason"] == "warning_mismatch"


def test_generated_and_published_evidence_match_schema_and_digest() -> None:
    contract = json.loads(
        (ROOT / "schemas/fas/slicer-reproducibility-evidence.schema.json").read_text(
            encoding="utf-8"
        )
    )
    example = json.loads(
        (ROOT / "examples/fas/slicer-reproducibility-evidence.example.json").read_text(
            encoding="utf-8"
        )
    )
    generated = evaluate([result("request:1"), result("request:2")])
    validator = Draft202012Validator(contract)

    Draft202012Validator.check_schema(contract)
    validator.validate(example)
    validator.validate(generated)
    assert example["evidence_digest"] == reproducibility_evidence_digest(example)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("can_authorize_production", True),
        ("can_upload", True),
        ("can_start_print", True),
        ("real_engine_runs_required", False),
    ],
)
def test_schema_rejects_authority_or_real_run_overstatement(field: str, value) -> None:
    contract = json.loads(
        (ROOT / "schemas/fas/slicer-reproducibility-evidence.schema.json").read_text(
            encoding="utf-8"
        )
    )
    example = json.loads(
        (ROOT / "examples/fas/slicer-reproducibility-evidence.example.json").read_text(
            encoding="utf-8"
        )
    )
    example[field] = value

    with pytest.raises(ValidationError):
        Draft202012Validator(contract).validate(example)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda values: values[:1],
        lambda values: [values[0], {**values[1], "status": "failed"}],
        lambda values: [
            values[0],
            {**values[1], "context": "twin"},
        ],
        lambda values: [
            values[0],
            {
                **values[1],
                "engine": {
                    **values[1]["engine"],
                    "build_digest": "9" * 64,
                },
            },
        ],
        lambda values: [values[0], {**values[1], "request_id": "request:1"}],
    ],
)
def test_incomparable_runs_fail_closed(mutation) -> None:
    values = [result("request:1"), result("request:2")]

    with pytest.raises(SlicerReproducibilityError):
        evaluate(mutation(deepcopy(values)))
