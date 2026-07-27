# Source-Import Legal Review Request

Status: Prepared for qualified external counsel; not yet signed or approved  
Requested scope: Importing and integrating the pinned OrcaSlicer source into
FORGE  
Prepared: 2026-07-27  
Related gate: Gate 1

This request asks qualified legal counsel to review the proposed source-import
boundary. It does not authorize source import, build, publication, or public
distribution. Until the review is completed and the conditions below are
accepted, the pinned Orca archive remains outside the trusted FORGE tree.

## Proposed source-import boundary

FORGE proposes to import only the reviewed, pinned OrcaSlicer source required
for a headless slicing worker, together with the dependencies, profiles, assets,
generated files, and notices proven reachable by the reproducible build. The
worker would be isolated from the FORGE kernel and would have no direct printer
discovery, cloud, upload, print-start, or authority-bearing capability.

The proposed v1 project expression is `AGPL-3.0-only`. The MCUT GPLv3 option is
the approved v1 default when MCUT is reachable in the worker build. The
commercial MCUT option is not selected. The optional non-free Bambu networking
plugin and binaries are excluded from the trusted source, build, package,
runtime, update, and test graphs.

## Evidence counsel should review

1. `docs/compliance/orcaslicer-upstream-provenance.md`
2. `docs/compliance/orcaslicer-v2.3.2-archive-inventory.md`
3. `docs/compliance/orcaslicer-v2.3.2-header-scan.md`
4. `docs/compliance/orcaslicer-v2.3.2-dependency-inventory.md`
5. `docs/compliance/orcaslicer-v2.3.2-license-compatibility-notes.md`
6. `docs/compliance/orcaslicer-v2.3.2-bambu-exclusion-scan.md`
7. `docs/compliance/sbom-baseline.json`
8. `docs/compliance/forge-provenance-audit-status.md`
9. `docs/compliance/GATE-1-LICENSING-DECISION-PACKET.md`
10. Root `LICENSE-STATUS.md`, `NOTICE`, `SOURCE-OFFER.md`, `CONTRIBUTING.md`,
    `TRADEMARKS.md`, `PRIVACY.md`, and `USER-DATA-TERMS.md`
11. The FORGE Constitution, decision register, slicer licensing worklist, and
    threat register
12. The pinned archive retained at the path and digest recorded in the
    provenance record

## Questions requiring written answers

### License and combined-work treatment

- Is importing the proposed Orca source into an AGPL-3.0-only FORGE
  distribution permissible under the pinned upstream and dependency licenses?
- Does the proposed worker boundary constitute a combined work, and what exact
  source, notices, installation information, and corresponding-source offer
  must be provided?
- Is the selected MCUT GPLv3 path compatible with the proposed worker and
  distribution? What files and notices must be included?
- Is any dependency, profile, asset, calibration pattern, translation, font,
  icon, generated file, or firmware interface incompatible or separately
  restricted?

### Exclusions and trademarks

- What evidence is sufficient to establish that Bambu networking source,
  binaries, downloads, runtime activation, and tests are absent?
- Which Bambu profiles, images, names, or other assets may be retained, and
  what attribution, permission, or trademark restrictions apply?
- Are the proposed FORGE, OrcaSlicer, and third-party trademark terms
  adequate for source, binary, hosted, and documentation distribution?

### Provenance and contributor rights

- Is the historical FORGE MIT reuse audit sufficient, and which notices or
  copyright statements must be preserved in imported or modified files?
- Are the DCO, inbound licensing, and contribution terms adequate for future
  Orca-derived modifications and corresponding-source publication?

### Distribution and service models

- Are the proposed local application, downloadable binary, update mechanism,
  container/package, and hosted service each compliant under the proposed
  license and source-offer plan?
- What user-facing notices, privacy disclosures, telemetry disclosures, data
  export terms, warranty disclaimers, and safety disclosures are required?

## Required legal-review result

Counsel should identify:

- reviewer/organization, qualifications, jurisdiction, and date;
- exact evidence commit and pinned archive digest reviewed;
- each legal conclusion and its assumptions;
- required remediation, owner, and acceptance evidence; and
- one of **approved for proposed source import**, **approved with conditions**,
  or **not approved**.

The result must be recorded in
`docs/compliance/LEGAL-REVIEW-RECORD.md`. “Approved with conditions” must list
conditions that are complete before import; conditions that apply only to
public distribution must be separately identified.

## No-import controls pending review

- Do not copy, vendor, build, or commit Orca-derived source into the trusted
  FORGE repository.
- Do not publish an integrated binary, hosted integrated service, or Orca-based
  source offer.
- Keep the pinned archive in isolated evidence storage and preserve its digest.
- Keep Gate 1 open even if repository tests and preliminary scans pass.
