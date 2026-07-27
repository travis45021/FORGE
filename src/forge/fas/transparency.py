"""In-product transparency resources for local FORGE interfaces."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any


class TransparencyError(ValueError):
    """Raised when a transparency resource is missing or misrepresented."""


_RESOURCES = (
    {
        "id": "license_status",
        "label": "License status",
        "path": "LICENSE-STATUS.md",
        "status": "pending_audit",
        "legal_review_required": True,
    },
    {
        "id": "notices",
        "label": "Notices and attributions",
        "path": "NOTICE",
        "status": "draft_incomplete",
        "legal_review_required": True,
    },
    {
        "id": "source_offer",
        "label": "Source and corresponding-source information",
        "path": "SOURCE-OFFER.md",
        "status": "draft_incomplete",
        "legal_review_required": True,
    },
    {
        "id": "privacy",
        "label": "Privacy principles",
        "path": "PRIVACY.md",
        "status": "draft",
        "legal_review_required": True,
    },
    {
        "id": "user_data_terms",
        "label": "Your data and ownership",
        "path": "USER-DATA-TERMS.md",
        "status": "draft",
        "legal_review_required": True,
    },
    {
        "id": "trademarks",
        "label": "Trademark policy",
        "path": "TRADEMARKS.md",
        "status": "draft",
        "legal_review_required": True,
    },
    {
        "id": "sbom",
        "label": "Software component inventory",
        "path": "docs/compliance/sbom-baseline.json",
        "status": "baseline_incomplete",
        "legal_review_required": False,
    },
)


class TransparencyCatalog:
    """Expose local compliance material without implying release clearance."""

    def resources(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "interface": "forge",
            "local_only": True,
            "public_distribution_cleared": False,
            "qualified_legal_review_complete": False,
            "resources": deepcopy(list(_RESOURCES)),
            "data_export": {
                "id": "export_user_data",
                "label": "Export my FORGE data",
                "action": "local.export_user_data",
                "scope_selection_required": True,
                "destination_selected_by_user": True,
                "network_required": False,
                "grants_physical_authority": False,
            },
            "accessible_label": (
                "Licensing, source, notices, privacy, user data, and export"
            ),
            "non_color_cue": "information",
        }

    def validate_repository(self, repository_root: str | Path) -> dict[str, Any]:
        """Confirm every catalog entry resolves inside the repository."""
        root = Path(repository_root).resolve()
        missing = []
        for resource in _RESOURCES:
            relative = PurePosixPath(resource["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise TransparencyError("transparency resource path is unsafe")
            target = (root / Path(*relative.parts)).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise TransparencyError(
                    "transparency resource leaves repository"
                ) from exc
            if not target.is_file():
                missing.append(resource["id"])
        if missing:
            raise TransparencyError(
                "transparency resources missing: " + ", ".join(sorted(missing))
            )
        return {
            "status": "available_with_disclosures",
            "resource_count": len(_RESOURCES),
            "public_distribution_cleared": False,
        }
