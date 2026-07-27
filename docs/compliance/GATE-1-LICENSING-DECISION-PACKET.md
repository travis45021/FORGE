# Gate 1 Licensing and Legal-Review Decision Packet

Status: Prepared for owner decision and qualified legal review  
Gate: Gate 1 — licensing, provenance, and release compliance  
Prepared: 2026-07-27

This packet turns the open Gate 1 work into a decision-ready record. It is an
engineering and evidence packet, not legal advice and not a legal sign-off.
No item below authorizes Orca source import, an integrated binary, a hosted
integrated service, or public distribution.

## 1. Decisions requiring owner approval

| Decision | Recommended starting position | Current state |
| --- | --- | --- |
| Integrated FORGE license | GNU AGPLv3, exact expression `AGPL-3.0-only` unless qualified counsel identifies a documented reason to permit later versions | **Open** |
| Orca relationship | Keep Orca-derived work in the same governed AGPLv3 distribution boundary; preserve all upstream notices and corresponding-source obligations | **Open for legal confirmation** |
| MCUT path | Use only the GPLv3 option unless counsel and procurement explicitly approve a separately documented commercial path | **Open** |
| Bambu networking | Exclude non-free networking source, binaries, downloads, runtime activation, and tests from the trusted build and release graph; treat profiles/assets separately | **Open; proof required** |
| Historical FORGE code | Reuse only after file-level mapping and preservation of applicable MIT notices | **Open** |
| User data | User retains ownership; local-first processing; sharing, telemetry, hosted operation, and community evidence are opt-in and separately disclosed | **Draft; legal confirmation required** |
| Trademark | FORGE marks remain controlled by the project; OrcaSlicer and Bambu marks are nominative/descriptive only and do not imply endorsement | **Draft; legal confirmation required** |
| Contributor terms | Require DCO/sign-off and inbound licensing terms consistent with the chosen project license and future source publication | **Draft; legal confirmation required** |

The recommendations are intentionally conservative defaults for review. They are
not final decisions until the owner records approval and qualified counsel
confirms the resulting package.

## 2. Evidence package provided to the reviewer

- `orcaslicer-upstream-provenance.md` — pinned v2.3.2 commit, URLs, and hashes.
- `orcaslicer-v2.3.2-archive-inventory.md` — isolated archive inventory.
- `orcaslicer-v2.3.2-header-scan.md` — preliminary file/header scan.
- `orcaslicer-v2.3.2-dependency-inventory.md` — dependency/profile baseline.
- `orcaslicer-v2.3.2-license-compatibility-notes.md` — preliminary observations.
- `orcaslicer-v2.3.2-bambu-exclusion-scan.md` — known exclusion gap.
- `sbom-baseline.json` — preliminary machine-readable inventory.
- `forge-provenance-audit-status.md` — historical FORGE reuse gap.
- `policy-prerequisite-status.md` — contributor, trademark, privacy, and data
  policy drafts.
- Root `LICENSE-STATUS.md`, `NOTICE`, `SOURCE-OFFER.md`, `CONTRIBUTING.md`,
  `TRADEMARKS.md`, `PRIVACY.md`, and `USER-DATA-TERMS.md`.
- `docs/governance/FORGE-DECISION-REGISTER.md`, the Constitution, and the
  production roadmap.

The pinned Orca archive remains outside the trusted FORGE tree. Its recorded
digest and source location must be independently reverified for the legal
review candidate.

## 3. Questions for qualified counsel

1. Is `AGPL-3.0-only` appropriate for the integrated FORGE application given
   the pinned Orca AGPLv3 source, historical FORGE MIT code, and the intended
   local and hosted deployment modes? If not, identify the exact alternative
   expression and why.
2. Does the selected MCUT GPLv3 option create any incompatibility, notice,
   source-offer, linking, or commercial-distribution obligation for the
   proposed worker and packaging boundary?
3. Which upstream dependencies, generated files, profiles, fonts, icons,
   translations, calibration patterns, firmware interfaces, and assets must
   be included in notices, source offers, or the SBOM?
4. What build, package, update, download, test, and runtime evidence is needed
   to prove that the non-free Bambu networking plugin and binaries are absent?
   Which Bambu profiles or assets require removal, attribution, or trademark
   restrictions?
5. What file-level treatment is required for reused historical FORGE MIT code,
   later FORGE changes, and mixed-license files?
6. Are the contributor/DCO, inbound licensing, trademark, privacy, user-data,
   telemetry, retention, export, and opt-in sharing drafts sufficient for the
   intended distribution and any hosted service?
7. What exact root license, `NOTICE`, corresponding-source offer, SBOM format,
   release metadata, and user-facing disclosures are required for binaries,
   hosted use, and source publication?
8. Are there jurisdiction-specific, export-control, warranty, safety, or
   consumer-disclosure issues that must be handled before a manufacturing
   application can control physical hardware?

## 4. Required reviewer deliverable

The reviewer must return a written memorandum or equivalent record that:

- identifies the reviewer/organization, qualifications, jurisdiction, and
  review date;
- names the exact evidence commit or release candidate reviewed;
- answers each question above or identifies a bounded follow-up;
- lists required remediation with owners and acceptance evidence; and
- states **approved**, **approved with conditions**, or **not approved** for
  the proposed source-import and public-distribution boundary.

The result must be transcribed into
`docs/compliance/LEGAL-REVIEW-RECORD.md`. A contract test passing, an assistant
recommendation, or an owner declaration cannot substitute for this review.

## 5. Gate 1 closure criteria

Gate 1 can close only when all of the following are true:

- the owner has recorded the exact project SPDX expression;
- file-level provenance, dependency, asset, and exclusion audits are complete;
- final root license, headers, notices, source offer, and SBOM match the actual
  release contents;
- contributor, trademark, privacy, and user-data policies are finalized;
- automated release checks pass against the release candidate; and
- the qualified legal review record is signed with no unresolved blocker.

Until then, the existing invariant remains in force: no Orca-derived source is
imported and no public integrated distribution is authorized.
