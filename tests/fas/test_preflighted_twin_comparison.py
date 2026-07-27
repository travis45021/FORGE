"""Tests for production/twin comparison of measured artifact evidence."""

import pytest

from forge.fas.preflight import paired_preflight_evidence_digest
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
            "build_digest": "d" * 64,
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


def paired_preflight() -> dict:
    result = {
        "schema_version": "1.0.0",
        "status": "ready_for_comparison",
        "input_digest": "d" * 64,
        "profile_digest": "e" * 64,
        "production": evidence("production"),
        "twin": evidence("twin"),
        "pair_outcome_validated": True,
        "both_output_digests_verified": True,
        "can_authorize_production": False,
        "can_upload": False,
        "can_start_print": False,
    }
    result["evidence_digest"] = paired_preflight_evidence_digest(result)
    return result


def test_paired_preflight_proof_is_carried_into_comparison() -> None:
    result = TwinComparisonService().compare_paired_preflight(
        comparison_id="comparison:paired",
        paired_preflight=paired_preflight(),
    )

    assert result["pair_preflight_verified"] is True
    assert result["acceptance"]["pair_preflight_required"] is True
    assert result["profile_digest"] == "e" * 64
    assert (
        result["pair_preflight_evidence_digest"]
        == paired_preflight()["evidence_digest"]
    )
    assert len(result["evidence_digest"]) == 64
    assert result["can_authorize_production"] is False


def test_rejects_boolean_user_review_shortcut() -> None:
    with pytest.raises(TwinComparisonError, match="click-three presentation"):
        TwinComparisonService().compare_paired_preflight(
            comparison_id="comparison:paired",
            paired_preflight=paired_preflight(),
            reviewed_by_user=True,
        )


def test_rejects_mutated_paired_preflight_evidence() -> None:
    pair = paired_preflight()
    pair["production"]["artifact_digest"] = "f" * 64

    with pytest.raises(TwinComparisonError, match="evidence digest"):
        TwinComparisonService().compare_paired_preflight(
            comparison_id="comparison:paired",
            paired_preflight=pair,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "failed_closed"),
        ("pair_outcome_validated", False),
        ("both_output_digests_verified", False),
        ("can_upload", True),
    ],
)
def test_rejects_uncoordinated_or_authoritative_pair(field: str, value: object) -> None:
    pair = paired_preflight()
    pair[field] = value

    with pytest.raises(TwinComparisonError, match="coordinated paired preflight"):
        TwinComparisonService().compare_paired_preflight(
            comparison_id="comparison:paired",
            paired_preflight=pair,
        )
