"""Fail-closed checks for the FORGE Gate 1 evidence baseline."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    ROOT / "CONSTITUTION.md",
    ROOT / "LICENSE-STATUS.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "TRADEMARKS.md",
    ROOT / "PRIVACY.md",
    ROOT / "USER-DATA-TERMS.md",
    ROOT / "docs/compliance/GATE-1-EVIDENCE-INDEX.md",
    ROOT / "docs/compliance/LEGAL-REVIEW-RECORD.md",
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
    if "Decision: **OPEN — not approved**" not in legal_record:
        print("legal review record must remain explicitly open until signed")
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
