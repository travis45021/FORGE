"""Tests for in-product transparency and user-data export access."""

from pathlib import Path

from forge.fas.transparency import TransparencyCatalog

ROOT = Path(__file__).resolve().parents[2]


def test_catalog_exposes_required_product_resources() -> None:
    catalog = TransparencyCatalog().resources()
    resource_ids = {resource["id"] for resource in catalog["resources"]}

    assert {
        "license_status",
        "notices",
        "source_offer",
        "privacy",
        "user_data_terms",
        "trademarks",
        "sbom",
        "security_threat_model",
        "security_threat_register",
    } <= resource_ids
    assert catalog["data_export"]["action"] == "local.export_user_data"
    assert catalog["data_export"]["destination_selected_by_user"] is True
    assert catalog["data_export"]["grants_physical_authority"] is False


def test_catalog_discloses_draft_and_legal_review_state() -> None:
    catalog = TransparencyCatalog().resources()

    assert catalog["public_distribution_cleared"] is False
    assert catalog["qualified_legal_review_complete"] is False
    assert any(
        resource["status"].startswith("draft") for resource in catalog["resources"]
    )


def test_every_catalog_resource_exists_in_repository() -> None:
    result = TransparencyCatalog().validate_repository(ROOT)

    assert result["status"] == "available_with_disclosures"
    assert result["resource_count"] == 9
    assert result["public_distribution_cleared"] is False
