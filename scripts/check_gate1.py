"""Fail-closed checks for the FORGE Gate 1 evidence baseline."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    ROOT / "CONSTITUTION.md",
    ROOT / "LICENSE-STATUS.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "TRADEMARKS.md",
    ROOT / "PRIVACY.md",
    ROOT / "USER-DATA-TERMS.md",
    ROOT / "NOTICE",
    ROOT / "SOURCE-OFFER.md",
    ROOT / "docs/compliance/GATE-1-EVIDENCE-INDEX.md",
    ROOT / "docs/compliance/FSF-LICENSING-OUTREACH-PACKET.md",
    ROOT / "docs/compliance/SOURCE-IMPORT-LEGAL-REVIEW-REQUEST.md",
    ROOT / "docs/compliance/LEGAL-REVIEW-RECORD.md",
    ROOT / "docs/compliance/orcaslicer-upstream-provenance.md",
    ROOT / "docs/compliance/orcaslicer-v2.3.2-bambu-exclusion-scan.md",
    ROOT / "docs/compliance/sbom-baseline.json",
    ROOT / "docs/compliance/upstream-orcaslicer-v2.3.2-LICENSE.txt",
)

ORCA_VERSION = "2.3.2"
ORCA_COMMIT = "c724a3f5f51c52336624b689e846c8fbc943a912"
SOURCE_ARCHIVE_SHA256 = (
    "2c7eea7b1e3757011f2c9520dc1712d789b9182b5c276aba271bf814172b0a52"
)
UPSTREAM_LICENSE_SHA256 = (
    "57c8ff33c9c0cfc3ef00e650a1cc910d7ee479a8bc509f6c9209a7c2a11399d6"
)


def main() -> int:
    missing = [path.relative_to(ROOT) for path in REQUIRED if not path.is_file()]
    if missing:
        for path in missing:
            print(f"missing required Gate 1 artifact: {path}")
        return 1

    legal_record = (ROOT / "docs/compliance/LEGAL-REVIEW-RECORD.md").read_text(
        encoding="utf-8"
    )
    if "Decision: **OPEN" not in legal_record or "not approved**" not in legal_record:
        print("legal review record must remain explicitly open until signed")
        return 1

    fsf_packet = (ROOT / "docs/compliance/FSF-LICENSING-OUTREACH-PACKET.md").read_text(
        encoding="utf-8"
    )
    if (
        "request for licensing guidance" not in fsf_packet
        or "no Orca source" not in fsf_packet
        or "imported into the trusted tree" not in fsf_packet
        or "AGPL-3.0-only" not in fsf_packet
        or "MCUT" not in fsf_packet
    ):
        print("FSF outreach packet must remain guidance-only and decision-complete")
        return 1

    import_request = (
        ROOT / "docs/compliance/SOURCE-IMPORT-LEGAL-REVIEW-REQUEST.md"
    ).read_text(encoding="utf-8")
    if (
        "not yet signed or approved" not in import_request
        or "Do not copy, vendor, build, or commit Orca-derived source"
        not in import_request
        or "AGPL-3.0-only" not in import_request
    ):
        print("source-import legal request must remain fail-closed pending review")
        return 1

    provenance = (ROOT / "docs/compliance/orcaslicer-upstream-provenance.md").read_text(
        encoding="utf-8"
    )
    for value, label in (
        (f"`v{ORCA_VERSION}`", "pinned upstream version"),
        (ORCA_COMMIT, "pinned upstream commit"),
        (SOURCE_ARCHIVE_SHA256, "source archive digest"),
        (UPSTREAM_LICENSE_SHA256, "upstream license digest"),
    ):
        if value not in provenance:
            print(f"provenance record is missing {label}")
            return 1

    license_bytes = (
        ROOT / "docs/compliance/upstream-orcaslicer-v2.3.2-LICENSE.txt"
    ).read_bytes()
    if sha256(license_bytes).hexdigest() != UPSTREAM_LICENSE_SHA256:
        print("archived upstream license digest does not match the reviewed value")
        return 1

    try:
        sbom = json.loads(
            (ROOT / "docs/compliance/sbom-baseline.json").read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError) as exc:
        print(f"SBOM baseline is unreadable: {exc}")
        return 1
    upstream = sbom.get("upstream", {})
    if (
        sbom.get("status") != "incomplete"
        or upstream.get("version") != ORCA_VERSION
        or upstream.get("commit") != ORCA_COMMIT
        or upstream.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256
    ):
        print("SBOM baseline does not match the pinned incomplete review state")
        return 1
    if not sbom.get("limitations") or not sbom.get("representative_components"):
        print("SBOM baseline must disclose limitations and reviewed components")
        return 1

    exclusion = (
        ROOT / "docs/compliance/orcaslicer-v2.3.2-bambu-exclusion-scan.md"
    ).read_text(encoding="utf-8")
    if "Status: Exclusion not established; Gate 1 remains open" not in exclusion:
        print("Bambu exclusion evidence must remain explicitly unresolved")
        return 1

    for path, required_status in (
        (ROOT / "LICENSE-STATUS.md", "final repository grant pending audit"),
        (ROOT / "PRIVACY.md", "qualified legal review required"),
        (ROOT / "USER-DATA-TERMS.md", "qualified legal review required"),
        (ROOT / "CONTRIBUTING.md", "qualified legal review required"),
        (ROOT / "TRADEMARKS.md", "qualified legal review required"),
    ):
        if required_status not in path.read_text(encoding="utf-8"):
            print(f"{path.name} must disclose its unresolved review status")
            return 1

    # Orca-derived source is intentionally forbidden in this contract-only tree.
    forbidden = tuple(ROOT.glob("**/OrcaSlicer-*/src"))
    if forbidden:
        for path in forbidden:
            print(f"forbidden Orca source-like path in trusted tree: {path}")
        return 1

    print("Gate 1 baseline checks passed; release remains blocked pending review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
