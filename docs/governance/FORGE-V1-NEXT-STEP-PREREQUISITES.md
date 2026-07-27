# FORGE v1.0 Next-Step Prerequisites

Status: Active completion checklist  
Authority: FORGE Constitution, production decision register, and the
canonical production roadmap  
Last reviewed: 2026-07-27

This is the ordered prerequisite list for the next FORGE production steps. A
checked item is evidence that the reference contract or repository work exists;
it is not, by itself, approval to claim a complete product or release. Items
requiring an external decision, qualified review, physical test, or public
artifact remain open until their evidence is recorded in the named authority
document.

## Release invariants

- No Orca-derived source, binary, profile, or integrated public distribution is
  imported or published before Gate 1 is closed.
- The final release decision is human-owned; no script, worker, simulation,
  twin, or model may self-approve, publish, upload, or start a print.
- Production and twin contexts remain isolated, and the four-click flow keeps
  the final user confirmation (`Yes, Print`) mandatory for v1.
- Optional vision and optional safety-sensor families are not v1 claims unless
  their evidence and review are explicitly added to the release scope.

## Ordered completion list

### 1. Gate 1 — licensing, provenance, and qualified legal review (first)

Complete and record all of the following in
`docs/governance/FORGE-SLICER-LICENSING-INTEGRATION-TODO.md` and
`docs/compliance/LEGAL-REVIEW-RECORD.md`:

- [ ] Confirm the pinned Orca release and exact commit, archive the source and
  license texts, and record retrieval URLs, dates, lengths, and SHA-256 hashes.
- [ ] Produce a file-level copyright, license-header, and SPDX inventory for
  all FORGE and imported material.
- [ ] Inventory third-party libraries, assets, icons, fonts, translations,
  profiles, calibration data, firmware interfaces, and generated content.
- [ ] Classify GPL, AGPL, permissive, public-domain, and separate components;
  document compatibility and distribution obligations for each.
- [ ] Prove the non-free Bambu networking plugin and binaries are absent from
  trusted source, build, packaging, and release artifacts.
- [ ] Audit historical FORGE MIT code reuse and preserve every required notice.
- [ ] Decide the exact FORGE SPDX expression (`AGPL-3.0-only` or
  `AGPL-3.0-or-later`) and record the decision in the decision register.
- [ ] Add the final root license and required per-file SPDX/copyright headers.
- [ ] Add `NOTICE`, third-party notices, corresponding-source/source-offer
  instructions, and a complete SBOM for the actual release contents.
- [ ] Define contributor sign-off/DCO, inbound licensing, trademark use,
  release-source publication, privacy, and user-data terms. These terms must
  preserve user ownership, local-first operation, explicit consent, and
  opt-in sharing.
- [ ] Obtain a qualified legal review of the complete package and record the
  reviewer qualifications, scope, findings, remediation, date, and approval or
  rejection in `LEGAL-REVIEW-RECORD.md`.
- [ ] Add automated release checks for license texts, notices, source match,
  excluded components, and SBOM completeness.
- [ ] Record the human Gate 1 decision authorizing (or refusing) Orca source
  import and public integrated distribution.

**Gate 1 exit evidence:** a reproducible source/provenance archive, final
license and notice package, SBOM, policy set, completed legal-review record,
passing release checks, and an explicit human authorization.

### 2. FAS-026 — durable local persistence

- [ ] Finish filesystem durability, encryption/key handling, crash-atomic
  transactions, backup/restore, migration, and recovery tests.
- [ ] Integrate the persistence contract into the application lifecycle and
  document retention, deletion, and export behavior.

### 3. FAS-027 — supervised service lifecycle

- [ ] Implement the production process supervisor, startup/shutdown ordering,
  health transitions, restart policy, and crash recovery.
- [ ] Prove resource limits, log/evidence retention, and operator-visible
  recovery actions in the packaged application.

### 4. FAS-028 — provider adapters and physical dispatch

- [ ] Implement capability-based adapters for supported and custom hardware.
- [ ] Prove authorization boundaries, unavailable-capability explanations,
  cancellation, and physical dispatch against real providers.

### 5. FAS-029 — motion calibration and HIL evidence

- [ ] Complete calibration workflows, limits, evidence capture, and repeated
  hardware-in-the-loop tests for motion providers.

### 6. FAS-030 — independent thermal safety

- [ ] Implement independent thermal cutoffs and prove sensor-failure,
  runaway, recovery, and power-loss behavior with HIL evidence.

### 7. FAS-031 — material handling

- [ ] Complete material calibration, load/unload, jam detection, recovery,
  retry, and operator-confirmed interruption evidence.

### 8. FAS-032 — optional vision

- [ ] Keep out of v1 scope unless claimed; if claimed, complete privacy,
  calibration, failure, and HIL evidence and add it to the release decision.

### 9. FAS-033 — integrated slicing and artifact validation

- [ ] After Gate 1 authorization, integrate the approved Orca worker through a
  quarantined boundary and complete engine-backed STEP/3MF normalization.
- [ ] Prove deterministic artifact preflight, provenance, warnings/failures,
  and reproducibility against real worker output.

### 10. FAS-034 — controlled upload, start, and monitoring

- [ ] Wire the upload, live-printer checks, mandatory final confirmation,
  controlled start, monitoring, cancellation, and outcome recording into the
  application.
- [ ] Prove no simulation, twin, provider, or background event can bypass the
  final user authorization.

### 11. FAS-035 — optional safety sensors

- [ ] Keep out of v1 scope unless claimed; if claimed, complete independent
  sensor validation, fault handling, and release evidence.

### 12. FAS-036 — packaging and compatibility

- [ ] Finish installer, upgrade, rollback, compatibility matrix, signed
  artifacts, corresponding source, SBOM, and recovery documentation.

### 13. Slicer Gates 2–3 — worker and contract integration

- [ ] Reproduce the pinned upstream Orca build and document the build boundary,
  source inputs, locked dependencies, and update policy.
- [ ] Select and review a headless worker; enforce process, filesystem,
  network, CPU, memory, timeout, and output-size isolation.
- [ ] Complete STEP/3MF quarantine, parser/normalization, Manufacturing Intent,
  slicer request/result/warning/failure, lineage, production/twin, and four-
  click contracts with real engine evidence.
- [ ] Remove or disable direct printer discovery, cloud, upload, and start
  capabilities from the trusted worker build.

### 14. Slicer Gates 4–5 — application integration

- [ ] Integrate real profile translation, slicing execution, artifact review,
  accessible UI, live checks, controlled upload/start, monitoring, and outcome
  recording.
- [ ] Validate the complete user flow for F3D-free approved inputs: STEP, 3MF,
  STL, and G-code, with plain-language errors and no hidden automation.

### 15. Slicer Gate 6 — assurance

- [ ] Complete security, hostile-content, fault, accessibility, deterministic
  reproducibility, resource-exhaustion, process-launcher, and HIL evidence.
- [ ] Verify the release package contains complete source, Orca notices,
  SBOM, exclusions, signatures, and source-to-wheel correspondence.

### 16. FAS-037 — final human v1 release decision

- [ ] Re-run the Constitution, licensing, privacy, safety, documentation,
  installation, recovery, and release audits.
- [ ] Obtain the final human release approval; publish only the approved
  integrated distribution and its corresponding source/evidence package.

## Approval bundle to bring forward together

The next approval packet should contain the exact SPDX choice, provenance and
dependency inventory, final license/NOTICE/source-offer/SBOM plan, contributor
and trademark policy, privacy and user-data terms, qualified legal-review
request, and the proposed Orca import/public-distribution boundary. Hardware
access and any optional vision or safety claims should be presented as separate
scope decisions.

## Canonical references

- `docs/governance/FORGE-SLICER-LICENSING-INTEGRATION-TODO.md`
- `docs/compliance/LEGAL-REVIEW-RECORD.md`
- `docs/governance/FORGE-PRODUCTION-ROADMAP.md`
- `docs/security/v1-threat-register.json`
- `docs/architecture/FAS-037-forge-v1-baseline-release-scope.md`
