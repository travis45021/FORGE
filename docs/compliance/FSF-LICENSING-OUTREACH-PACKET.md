# FORGE Licensing Outreach Packet for the FSF

Prepared: 2026-07-27  
Repository evidence commit: `283724f`  
Purpose: request educational licensing/compliance guidance from the Free
Software Foundation Licensing and Compliance Lab

This packet is designed to accompany an email to `licensing@fsf.org`. It is a
request for licensing guidance, not a claim that the FSF represents FORGE or a
substitute for an attorney-client relationship. FORGE will obtain qualified
legal counsel before source import or public integrated distribution.

## 1. Project summary

FORGE is an open, local-first, capability-based manufacturing and 3D-printing
control and assurance platform. It is intended to support known and custom
printers without making a manufacturer or cloud service the authority boundary.
The FORGE Constitution requires evidence before significant action, explicit
user authority, explainability, hardware neutrality, local operation, and open
interoperable interfaces.

FORGE is not trying to publish a standalone OrcaSlicer fork. The approved plan
is to integrate an OrcaSlicer-derived slicing engine as a governed capability
inside FORGE. FORGE retains authority over Objects, Missions, verification,
the Operational Twin, Runtime, provider boundaries, user confirmation, and
physical dispatch.

## 2. Proposed integration

- Upstream: OrcaSlicer `v2.3.2`.
- Pinned commit: `c724a3f5f51c52336624b689e846c8fbc943a912`.
- Proposed worker: a headless, isolated slicing worker derived from the pinned
  source.
- Initial design inputs: STEP and 3MF; full F3D project support is deferred.
- Execution contexts: one maintained engine codebase with isolated production
  and twin workspaces.
- User flow: four actions, with mandatory **Yes, Print** after live printer
  checks and before controlled upload/start.
- Worker restrictions: no direct printer discovery, cloud, upload, print-start,
  or authority-bearing capability.
- Current state: contract-only FORGE repository; no Orca source has been
  imported into the trusted tree.

## 3. Decisions already made

- FORGE project expression: **GNU `AGPL-3.0-only`**, owner-confirmed.
- MCUT: use the upstream GPLv3 option if reachable in the worker build; the
  commercial option is not selected for v1.
- Non-free Bambu networking: excluded from trusted source, build, package,
  runtime, update, and test graphs.
- User files, profiles, local knowledge, evidence, and produced artifacts
  remain user-owned unless explicitly shared under separate terms.
- The FORGE Constitution outranks implementation convenience or vendor
  preference.

These are project decisions, not legal conclusions. The exact file-level
treatment, combined-work analysis, and release obligations remain open.

## 4. Upstream evidence

The pinned archive is retained outside the trusted repository and is identified
in the provenance record by its source URL, byte length, and SHA-256 digest.
The repository contains the following preliminary evidence:

- `docs/compliance/orcaslicer-upstream-provenance.md`
- `docs/compliance/orcaslicer-v2.3.2-archive-inventory.md`
- `docs/compliance/orcaslicer-v2.3.2-header-scan.md`
- `docs/compliance/orcaslicer-v2.3.2-dependency-inventory.md`
- `docs/compliance/orcaslicer-v2.3.2-license-compatibility-notes.md`
- `docs/compliance/orcaslicer-v2.3.2-bambu-exclusion-scan.md`
- `docs/compliance/sbom-baseline.json`
- `docs/compliance/upstream-orcaslicer-v2.3.2-LICENSE.txt`

The evidence currently shows a mixed dependency tree, including GPL,
permissive, weak-copyleft, assets, profiles, translations, generated content,
and explicit Bambu networking source members. These are observations requiring
classification, not final legal findings.

## 5. Questions for FSF guidance

Please help us understand the following, especially under the AGPL/GPL family:

1. Is `AGPL-3.0-only` a coherent project expression for an application that
   incorporates an OrcaSlicer-derived worker whose upstream project is AGPLv3?
2. How should FORGE treat the boundary between the AGPL FORGE application and
   the Orca-derived worker when distributed together or run as a hosted service?
3. What source, installation-information, notice, and corresponding-source
   obligations should we plan for the combined distribution?
4. How should the MCUT GPLv3 option be documented and classified if MCUT is
   linked into the worker? What should we verify before importing it?
5. How should GPL, LGPL, MPL, permissive, public-domain, generated, profile,
   font, icon, translation, calibration, and firmware-interface material be
   represented in notices and an SBOM?
6. What is a defensible compliance method for proving that the non-free Bambu
   networking plugin and binaries are absent from source, build, packaging,
   download, update, runtime, and test graphs?
7. What notices and attribution treatment should apply to Bambu profiles/assets
   that are not networking code, and which questions require trademark counsel?
8. How should historical FORGE MIT code and later AGPL-covered modifications be
   marked at file and component level?
9. Are the proposed DCO/inbound licensing and corresponding-source practices
   reasonable for a small community project?
10. Which matters are outside FSF licensing guidance and must go to retained
    counsel—for example privacy, trademarks, product liability, safety,
    export controls, or commercial contracts?

## 6. Specific source-import question

Before FORGE imports any Orca-derived source, what minimum evidence and review
would FSF recommend for this boundary?

- pinned source and license archive;
- file-level copyright/license/SPDX inventory;
- dependency and asset reachability map;
- MCUT option and license record;
- Bambu exclusion proof;
- final root license and per-file treatment;
- `NOTICE`, third-party notices, and corresponding-source instructions;
- reproducible build and SBOM linkage; and
- an independent legal review record.

## 7. Current controls

Until the review is complete, FORGE will:

- keep the Orca archive outside the trusted FORGE tree;
- prohibit Orca-derived source import, build, and public distribution;
- keep the Bambu networking plugin outside the trusted baseline;
- preserve upstream and historical FORGE notices; and
- keep Gate 1 and the legal-review record open.

## 8. Requested response

We are not asking the FSF to approve FORGE for release or to provide a formal
legal opinion. We are asking for:

- pointers to the correct GPL/AGPL guidance;
- identification of obvious compliance risks in the proposed boundary;
- recommended practices for source offers, notices, and combined-work records;
- confirmation of which questions require a retained open-source attorney; and
- any recommended changes before we approach counsel or import source.

## 9. Attachments / links to include

Send this packet together with, or link to, the following files:

- `docs/compliance/SOURCE-IMPORT-LEGAL-REVIEW-REQUEST.md`
- `docs/compliance/GATE-1-LICENSING-DECISION-PACKET.md`
- `docs/compliance/GATE-1-EVIDENCE-INDEX.md`
- `docs/compliance/LEGAL-REVIEW-RECORD.md`
- `docs/governance/FORGE-DECISION-REGISTER.md`
- `docs/governance/FORGE-SLICER-LICENSING-INTEGRATION-TODO.md`
- `CONSTITUTION.md`
- `LICENSE-STATUS.md`
- `NOTICE`
- `SOURCE-OFFER.md`
- `CONTRIBUTING.md`
- `TRADEMARKS.md`
- `PRIVACY.md`
- `USER-DATA-TERMS.md`

Do not send private keys, credentials, personal user data, unreleased customer
designs, or the external archive path if sharing the packet publicly. Replace
the repository evidence commit above with the exact commit supplied to FSF.
