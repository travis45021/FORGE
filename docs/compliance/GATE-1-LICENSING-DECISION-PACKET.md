# Gate 1 Licensing and Legal-Review Decision Packet

Status: Prepared for owner decision and qualified legal review  
Gate: Gate 1 — licensing, provenance, and release compliance  
Prepared: 2026-07-27

This packet turns the open Gate 1 work into a decision-ready record. It is an
engineering and evidence packet, not legal advice and not a legal sign-off.
No item below authorizes Orca source import, an integrated binary, a hosted
integrated service, or public distribution.

## 1. Decisions in order

### 1.1 MCUT licensing decision — first remaining decision

MCUT is presented upstream with a mutually exclusive GPLv3 path and a
commercial path. FORGE's open-distribution default is the GPLv3 path: it keeps
the dependency auditable and avoids introducing a separately negotiated,
proprietary grant into the trusted worker. That choice still requires a
reachability audit, preservation of MCUT notices/source obligations, and legal
confirmation that the selected worker boundary and final distribution satisfy
the applicable GPL terms. A commercial MCUT license is not assumed and cannot
be selected implicitly; it would require separate procurement, contract
review, and an updated notice/SBOM record.

**Owner position:** use the MCUT GPLv3 option unless qualified counsel and
procurement approve a documented commercial alternative. **Status: Open for
evidence and legal confirmation.**

#### Simplest route

1. Keep MCUT inside the isolated, headless Orca worker rather than making it a
   FORGE kernel dependency.
2. Select and document MCUT's GPLv3 option; do not negotiate or ship the
   commercial option for v1.
3. Verify whether the pinned worker actually builds and links MCUT, then record
   the reachable files, notices, source-offer obligations, and SBOM entries.
4. Keep the worker unable to discover printers, upload, start, or contact cloud
   services. FORGE remains the only authority-bearing layer.
5. Have qualified counsel confirm the combined-work, linking, notice, and
   corresponding-source treatment before import or distribution.

This is the lowest-complexity route because it avoids a second commercial
license negotiation and keeps one auditable open-source compliance boundary.
It is not a conclusion that every MCUT use is legally compatible; the build
reachability and legal review remain required.

#### Long-term FORGE fit

The GPLv3 route does not conflict with FORGE's stated long-term goals of an
open, inspectable, user-controlled, local-first ecosystem. It supports the
existing AGPL direction, preserves source availability, and avoids tying core
capabilities to a vendor contract. The isolation boundary also protects
FORGE's hardware-neutral kernel and keeps MCUT replaceable.

The commercial route would create more long-term risk: vendor dependency,
restricted redistribution, a split source/binary story, and possible conflict
with FORGE's open-ecosystem and corresponding-source commitments. It should be
considered only if the GPLv3 path fails a documented technical or legal need
and counsel confirms the resulting boundary.

### 1.2 Exact FORGE project license

**Owner-confirmed:** GNU `AGPL-3.0-only`. This records the project's chosen
version expression and does not by itself complete the file-level audit, final
license grant, or legal sign-off. **Status: Owner confirmed; legal
compatibility confirmation required.**

### 1.3 Orca relationship and distribution boundary

Keep Orca-derived work in the governed AGPLv3 distribution boundary, preserve
all upstream notices and corresponding-source obligations, and do not import or
publish it until Gate 1 closes. **Status: Open for legal confirmation.**

### 1.4 Non-free Bambu networking exclusion

Exclude non-free networking source, binaries, downloads, runtime activation, and
tests from the trusted build and release graph. Treat Bambu profiles and assets
as a separate attribution and trademark review. **Status: Open; proof required.**

### 1.5 Historical FORGE provenance

Reuse historical FORGE MIT code only after file-level mapping and preservation
of applicable notices, authorship, and transformations. **Status: Open.**

### 1.6 User-data terms

Users retain ownership; processing is local-first; sharing, telemetry, hosted
operation, and community evidence are opt-in and separately disclosed. **Status:
Draft; legal confirmation required.**

### 1.7 Trademark treatment

FORGE marks remain controlled by the project. OrcaSlicer and Bambu marks are
nominative/descriptive only and must not imply endorsement. **Status: Draft;
legal confirmation required.**

### 1.8 Contributor and inbound licensing

Require DCO/sign-off and inbound licensing terms consistent with
`AGPL-3.0-only` and future corresponding-source publication. **Status: Draft;
legal confirmation required.**

The owner-confirmed license expression is recorded now; all other positions are
conservative starting positions until their evidence and qualified legal review
are complete.

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
