# FORGE Slicer and Licensing Integration To-Do

Status: Active prerequisite worklist  
Effective date: 2026-07-26  
Decision authority: `ADR-001-orcaslicer-slicing-foundation.md`

This is the ordered implementation list for the approved OrcaSlicer-derived
foundation. A checked item is complete in the production repository. Items are
gates, not suggestions: later gates may be explored, but their outputs may not
be released or granted physical authority before their prerequisites pass.

## Gate 0 - Bind the approved direction

- [x] Record OrcaSlicer as the upstream slicing foundation.
- [x] Record one engine codebase with isolated production and twin contexts.
- [x] Record STEP and 3MF as the initial integrated design inputs.
- [x] Defer full F3D project support.
- [x] Record the mandatory four-click v1 path, including **Yes, Print** after
  live printer checks and before controlled upload or start.
- [x] Keep every bypass path disabled for v1.
- [x] Record GNU AGPL version 3 as the project licensing direction.
- [x] Exclude the optional non-free Bambu networking plugin from the trusted
  baseline.

## Gate 1 - Licensing, provenance, and release compliance

No Orca-derived source is imported and no public binary or hosted integrated
release is distributed until the applicable items in this gate are complete.

- [x] Pin the reviewed OrcaSlicer release tag and exact source commit
  (`v2.3.2`,
  `c724a3f5f51c52336624b689e846c8fbc943a912`).
- [ ] Archive the upstream license files and record the source URL and digest.
- [ ] Perform a file-level copyright, license-header, and SPDX inventory.
- [ ] Inventory third-party libraries, assets, icons, fonts, translations,
  profiles, calibration patterns, firmware interfaces, and generated content.
- [ ] Identify GPL, AGPL, permissive, public-domain, and separately licensed
  material; document compatibility and redistribution obligations.
- [ ] Prove that the optional non-free Bambu networking plugin and its binaries
  are absent from the trusted build and packaging graph.
- [ ] Audit historical FORGE MIT code that will be reused and preserve its
  notices.
- [ ] Decide the exact FORGE SPDX expression, including `AGPL-3.0-only` versus
  `AGPL-3.0-or-later`, from the audit evidence.
- [ ] Add the final root license text and per-file SPDX/copyright headers.
- [ ] Add `NOTICE`, third-party notices, source-offer/corresponding-source
  instructions, and an SBOM.
- [ ] Define contributor sign-off/DCO, inbound licensing, trademark, and
  release-source publication rules.
- [ ] Add plain-language privacy and user-data terms confirming user ownership
  and opt-in sharing.
- [ ] Obtain qualified legal review before the first public integrated release.
- [ ] Add automated release checks for license texts, notices, source match,
  excluded components, and SBOM completeness.

## Gate 2 - Upstream engineering spike

- [ ] Reproduce an unmodified build of the pinned OrcaSlicer source.
- [ ] Map slicer-core, GUI, profile, networking, update, telemetry, and
  printer-control boundaries.
- [ ] Select the smallest maintainable headless worker boundary.
- [ ] Define the upstream synchronization and security-update policy.
- [ ] Measure startup, slicing time, memory, disk, and deterministic-output
  behavior on representative STEP and 3MF fixtures.
- [ ] Prove two isolated worker contexts can run from one maintained engine
  codebase.
- [ ] Disable or remove direct printer discovery, cloud, upload, and print-start
  paths from the trusted worker build.

## Gate 3 - FORGE contracts and state machine

- [ ] Specify STEP and 3MF quarantine, parsing, normalization, and validation.
- [ ] Define the Manufacturing Intent object and loss/ambiguity reporting.
- [ ] Define versioned slicer request, result, warning, and failure contracts.
- [ ] Record source digest, engine build, derived profile digest, context,
  settings, warnings, and output digest for reproducibility.
- [ ] Specify production-versus-twin comparison evidence and acceptance rules.
- [ ] Implement the four-click state machine:
  1. add file;
  2. confirm context;
  3. create verified Print Mission;
  4. after live printer checks and before upload, require **Yes, Print**.
- [ ] Represent the final-confirmation bypass capability as disabled for every
  v1 role and mode.
- [ ] Prove no slicing result, simulation result, or UI event can grant Mission
  authority.

## Gate 4 - Governed integration

- [ ] Build the adapter from verified FORGE Objects and configuration to an
  ephemeral Orca worker profile.
- [ ] Run the production and twin contexts with separate workspaces, inputs,
  outputs, logs, resource limits, and cancellation.
- [ ] Add deterministic artifact preflight and production/twin comparison.
- [ ] Connect accepted artifacts to the Executive and Runtime Mission path.
- [ ] Add capability-provider upload only after the mandatory final user gate.
- [ ] Keep printer-specific behavior in replaceable capability providers, with
  Moonraker/Klipper only as the first tested reference.

## Gate 5 - Unified user experience

- [ ] Implement one FORGE interface rather than exposing a second slicer app.
- [ ] Provide plain-language STEP/3MF import status and ambiguity resolution.
- [ ] Show inferred printer, material, process, and safety context before click
  two.
- [ ] Show verification, twin comparison, warnings, and limitations before
  click three.
- [ ] Show live printer checks and the mandatory **Yes, Print** action before
  controlled upload/start.
- [ ] Meet FAS-024 accessibility, structured error, and interface parity
  requirements.
- [ ] Provide license, source, notices, privacy, and data-export access inside
  the product.

## Gate 6 - Assurance and release

- [ ] Add unit, contract, schema, scenario, fault-injection, security,
  accessibility, reproducibility, and hardware-in-the-loop coverage.
- [ ] Test hostile and malformed STEP/3MF content in isolation.
- [ ] Test worker crashes, timeouts, resource exhaustion, cancellation, and
  stale context.
- [ ] Prove that twin evidence cannot authorize production.
- [ ] Prove that historical replay cannot upload or start a print.
- [ ] Prove that no v1 path skips the fourth click.
- [ ] Verify that shipped binaries correspond to the published complete source.
- [ ] Pass FAS-025 release assurance and the licensing compliance checks.
- [ ] Document supported upstream version, known limitations, rollback, and
  recovery.

## Canonical sequencing

FAS-036 has an implemented reference contract. FAS-037 is now the next
canonical specification. Gate 0 is complete. Gate 1 remains active and blocks
Orca source import and public integrated distribution. Filesystem durability,
encryption, crash-atomic transactions, and application integration remain
required before the FAS-026 contract is a v1 product capability.
