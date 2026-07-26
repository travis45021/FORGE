import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "docs/architecture/ADR-001-orcaslicer-slicing-foundation.md"
TODO = (
    ROOT
    / "docs/governance/FORGE-SLICER-LICENSING-INTEGRATION-TODO.md"
)
REGISTER = ROOT / "docs/governance/FORGE-DECISION-REGISTER.md"
ROADMAP = ROOT / "docs/governance/FORGE-PRODUCTION-ROADMAP.md"
PROVENANCE = ROOT / "docs/compliance/orcaslicer-upstream-provenance.md"
LICENSE_STATUS = ROOT / "LICENSE-STATUS.md"


def compact(value):
    return re.sub(r"\s+", " ", value)


class SlicerFoundationGovernanceTests(unittest.TestCase):
    def test_approved_boundaries_are_recorded(self):
        adr = ADR.read_text(encoding="utf-8")
        for required in (
            "OrcaSlicer",
            "production context",
            "twin context",
            "STEP",
            "3MF",
            "F3D",
            "Yes, Print",
            "GNU AGPL version 3",
            "user-owned",
            "non-free Bambu networking plugin",
        ):
            self.assertIn(required, adr)

    def test_final_confirmation_follows_live_checks_and_precedes_upload(self):
        adr = ADR.read_text(encoding="utf-8")
        workflow = adr[adr.index("### 3. Mandatory four-click") :]
        final_step = workflow[workflow.index("4. After live printer checks") :]
        self.assertLess(final_step.index("live printer checks"), final_step.index("Yes, Print"))
        self.assertLess(final_step.index("Yes, Print"), final_step.index("upload"))

    def test_v1_bypass_is_disabled(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (ADR, TODO, REGISTER)
        )
        self.assertIn("disabled for every v1 user", combined)
        self.assertIn("no v1 path skips the fourth click", combined)

    def test_license_gate_blocks_import_and_public_distribution(self):
        todo = compact(TODO.read_text(encoding="utf-8"))
        status = compact(LICENSE_STATUS.read_text(encoding="utf-8"))
        self.assertIn("No Orca-derived source is imported", todo)
        self.assertIn("do not import Orca-derived source", status)
        self.assertIn("do not distribute a public integrated binary", status)
        self.assertIn("exact SPDX expression", status)

    def test_pinned_upstream_evidence_is_not_mistaken_for_completed_audit(self):
        provenance = compact(PROVENANCE.read_text(encoding="utf-8"))
        self.assertIn("v2.3.2", provenance)
        self.assertIn(
            "c724a3f5f51c52336624b689e846c8fbc943a912",
            provenance,
        )
        self.assertIn("file-level audit incomplete", provenance)
        self.assertIn("does not approve source import", provenance)

    def test_fas_028_is_next(self):
        mapping = json.loads(
            (
                ROOT / "docs/governance/fas-reconciliation-map.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(mapping["rules"]["next_canonical_id"], "FAS-028")
        self.assertIn(
            "FAS-028 is the next canonical specification",
            compact(ROADMAP.read_text(encoding="utf-8")),
        )


if __name__ == "__main__":
    unittest.main()
