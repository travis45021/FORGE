"""Tests for production/twin comparison of measured artifact evidence."""

import pytest

from forge.fas.twin_comparison import TwinComparisonError, TwinComparisonService


def evidence(context: str, artifact: str = "a") -> dict:
    return {
        "request_id": f"request:{context}",
        "context": context,
        "artifact_digest": artifact * 64,
        "engine": {
            "name": "reviewed-engine",
            "version": "pinned",
            "source_digest": "c" * 64,
        },
        "warnings": [],
        "status": "passed",
        "result_contract_validated": True,
        "output_digest_verified": True,
        "can_authorize_production": False,
        "can_upload": False,
        "can_start_print": False,
    }


def compare(production: dict, twin: dict) -> dict:
    return TwinComparisonService().compare_preflighted(
        comparison_id="comparison:measured",
        input_digest="d" * 64,
        production=production,
        twin=twin,
    )


def test_matching_preflighted_bytes_produce_non_authoritative_match() -> None:
    result = compare(evidence("production"), evidence("twin"))

    assert result["acceptance"]["status"] == "matching"
    assert result["acceptance"]["preflight_evidence_required"] is True
    assert result["production"]["preflight_verified"] is True
    assert result["twin"]["preflight_verified"] is True
    assert result["can_authorize_production"] is False


def test_measured_artifact_difference_is_reported() -> None:
    result = compare(evidence("production", "a"), evidence("twin", "b"))

    assert result["acceptance"]["status"] == "different"
    assert result["differences"] == ["artifact_digest"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "failed"),
        ("output_digest_verified", False),
        ("can_upload", True),
    ],
)
def test_rejects_unverified_or_authoritative_preflight(
    field: str, value: object
) -> None:
    production = evidence("production")
    production[field] = value

    with pytest.raises(TwinComparisonError, match="deterministic preflight"):
        compare(production, evidence("twin"))


def test_rejects_swapped_preflight_contexts() -> None:
    with pytest.raises(TwinComparisonError, match="context"):
        compare(evidence("twin"), evidence("production"))
