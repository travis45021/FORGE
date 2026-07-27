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
- [x] Archive the upstream license and pinned source files; record their source
  URLs, byte length, and verified SHA-256 digests.
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
- [ ] Obtain and record qualified legal review before any v1 public integrated
  distribution, including binaries, hosted service, or Orca-derived source
  publication (`docs/compliance/LEGAL-REVIEW-RECORD.md`).
- [ ] Add automated release checks for license texts, notices, source match,
  excluded components, and SBOM completeness. A contract-only baseline check
  exists at `scripts/check_gate1.py`; it verifies committed license bytes,
  pin/digest consistency, policy disclosures, unresolved exclusion/legal state,
  and preliminary SBOM structure. Build/source matching, exclusion proof, and
  final SBOM completeness remain open.

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
  Quarantine assessment, bounded structural parsing, deterministic normalized
  digests, XML protections, and 3MF path-traversal rejection are implemented;
  engine-backed geometry normalization remains open.
- [x] Define the Manufacturing Intent object and loss/ambiguity reporting.
- [x] Define versioned slicer request, result, warning, and failure contracts.
- [x] Record source digest, engine build, derived profile digest, context,
  settings, warnings, and output digest for reproducibility.
- [x] Specify production-versus-twin comparison evidence and acceptance rules.
- [x] Implement the four-click state machine:
  1. add file;
  2. confirm context;
  3. create verified Print Mission;
  4. after live printer checks and before upload, require **Yes, Print**.
- [x] Represent the final-confirmation bypass capability as disabled for every
  v1 role and mode.
- [x] Prove no slicing result or simulation/twin result can grant Mission
  authority.

## Gate 4 - Governed integration

- [ ] Build the adapter from verified FORGE Objects and configuration to an
  ephemeral Orca worker profile. A deterministic hardware-neutral adapter now
  derives data-only ephemeral profiles and rejects unknowns, endpoints,
  credentials, cloud, and capability mismatch. Slicer preparation requires the
  derived profile and rejects arbitrary digests or authority-bearing settings;
  real Orca profile translation remains open.
- [ ] Run the production and twin contexts with separate workspaces, inputs,
  outputs, logs, resource limits, and cancellation. Manifest isolation and
  resource validation are implemented. Single-use assignments now bind each
  context to its exact request and ephemeral profile. Paired assignments
  require one reviewed engine build, identical input/profile digests, separate
  workspaces, and no hardware authority. Any failed worker fails the pair,
  cancels the sibling path, and blocks preflight/comparison; real worker
  execution remains open.
- [ ] Add deterministic artifact preflight and production/twin comparison.
  Byte-to-result digest, request, context, provenance, comparison, and
  acceptance reference services are implemented. Paired preflight now requires
  a successful coordinated worker-pair outcome, verifies both output byte
  digests against that outcome, and binds both results to the same reviewed
  engine before comparison. Comparison and acceptance now require and preserve
  the paired-preflight proof, closing the individually preflighted evidence
  bypass. Fourth-click, Executive, controlled transport, and Runtime boundaries
  preserve and recheck both deterministic and coordinated-pair preflight proof.
  Accepted output also remains bound to its exact source-input and ephemeral
  profile digests through dispatch. Result schema, preflight, and comparison
  require the exact reviewed engine source and binary-build digests. Acceptance,
  fourth-click, Executive, transport, and Runtime preserve and recheck those
  engine digests. The complete paired comparison is canonically hashed after
  review, and that digest is required through fourth-click dispatch so warnings
  or evidence cannot change silently. Acceptance requires a named, timestamped
  click-three review receipt bound to that digest; a boolean review shortcut is
  rejected. The click-three reviewer and time remain distinct from, and are
  preserved alongside, the fourth-click confirmer through Executive, transport,
  and Runtime. The fourth click also requires and preserves its own explicit
  confirmation timestamp. Both timestamps must be valid UTC, click three must
  precede click four, and Runtime rejects future confirmation evidence. The
  fourth-click token has an explicit short-lived validity window and cannot
  dispatch at or after expiry. Live printer checks also have their own
  timestamps and expiry, must precede confirmation, and must remain fresh
  through Runtime dispatch. The complete provider-neutral live-check record is
  canonically hashed and that digest is preserved through dispatch, preventing
  silent mutation after collection. The final-confirmation token is also hashed
  with the exact job, artifact lineage, comparison, live checks, actor, and
  validity window; token transplantation fails closed. Real engine artifact
  evidence remains open.
- [ ] Connect accepted artifacts to the Executive and Runtime Mission path.
  Evidence-bound Executive handoff and Runtime upload dispatch are implemented;
  application integration remains open.
- [x] Add capability-provider upload only after the mandatory final user gate.
- [ ] Keep printer-specific behavior in replaceable capability providers, with
  Moonraker/Klipper only as the first tested reference. Hardware-neutral and
  Moonraker/Klipper reference manifests are implemented with no compatibility
  boundary; real provider adapters and hardware tests remain open.

## Gate 5 - Unified user experience

- [ ] Implement one FORGE interface rather than exposing a second slicer app.
  One presentation-neutral FORGE print-interface contract now covers every
  stage and mode without exposing a slicer interface; application rendering
  remains open.
- [ ] Provide plain-language STEP/3MF import status and ambiguity resolution.
  A presentation-neutral, accessible status and user-resolution contract is
  implemented; application rendering remains open.
- [ ] Show inferred printer, material, process, and safety context before click
  two. A plain-language, accessible, fail-closed click-two presentation and
  confirmation contract is implemented; application rendering remains open.
- [ ] Show verification, twin comparison, warnings, and limitations before
  click three. A plain-language, accessible, fail-closed click-three review
  contract is implemented; application rendering remains open.
- [ ] Show live printer checks and the mandatory **Yes, Print** action before
  controlled upload/start. A plain-language, accessible, fail-closed click-four
  presentation contract is implemented; application rendering remains open.
- [ ] Meet FAS-024 accessibility, structured error, and interface parity
  requirements. Mode-parity screens, keyboard and screen-reader semantics,
  non-color cues, and actionable structured errors are implemented as
  contracts; application conformance remains open.
- [ ] Provide license, source, notices, privacy, and data-export access inside
  the product. A local transparency catalog exposes each resource, its draft
  or audit status, and user-directed export without implying legal clearance;
  application rendering remains open.

## Gate 6 - Assurance and release

- [ ] Add unit, contract, schema, scenario, fault-injection, security,
  accessibility, reproducibility, and hardware-in-the-loop coverage.
- [ ] Test hostile and malformed STEP/3MF content in isolation. 3MF path
  traversal, absolute/drive paths, symbolic links, compression bombs, XML
  entities/DOCTYPE, duplicate members, and malformed structures are covered.
  STEP size, binary/NUL, invalid-text, oversized-line, header, and structural
  checks are covered. Engine-backed geometry fixture coverage remains open.
- [ ] Test worker crashes, timeouts, resource exhaustion, cancellation, and
  stale context. Deterministic supervisor fault-injection contracts cover each
  failure and deny artifact/physical authority; real worker-process tests
  remain open.
- [x] Prove that twin evidence cannot authorize production.
- [x] Prove that historical replay cannot upload or start a print.
- [x] Prove that no v1 path skips the fourth click for every implemented
  contract path.
- [ ] Verify that shipped binaries correspond to the published complete source.
- [ ] Pass FAS-025 release assurance and the licensing compliance checks.
- [x] Document supported upstream version, known limitations, rollback, and
  recovery (`docs/releases/README-SLICER-INTEGRATION-v1.md`).

## Canonical sequencing

FAS-036 has an implemented reference contract. FAS-037 is implemented, and the
final human release gate is the remaining canonical decision. Gate 0 is
complete. Gate 1 remains active and blocks
Orca source import and public integrated distribution. Filesystem durability,
encryption, crash-atomic transactions, and application integration remain
required before the FAS-026 contract is a v1 product capability.
