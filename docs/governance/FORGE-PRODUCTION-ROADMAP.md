# FORGE Canonical Production Roadmap

Status: Reconciled production baseline  
Version: 1.0.0  
Effective date: 2026-07-25  
Baseline commit: `4966cbc1d84a30707c821b2d559f8f20fb842237`

## 1. Purpose

This roadmap reconciles the accepted historical FAS-001–036 architecture ledger
with the current production repository. It assigns one conflict-free canonical
number to every unimplemented historical concept while preserving current
FAS-001–009 and their Git history.

The machine-readable companion is `fas-reconciliation-map.json`.

## 2. Reconciliation rules

1. Current production FAS-001–009 keep their identifiers and meanings.
2. Historical FAS-001–007 map directly to current production FAS-001–007.
3. Historical FAS-008 Trust Framework and Sentinel becomes canonical FAS-010.
4. Historical FAS-009 Policy, Authority, and Automation Governance is absorbed
   by current FAS-008 Authorization Engine and FAS-009 Policy Bundle Governance.
   Unimplemented user-delegation details remain requirements for later
   specifications, but historical FAS-009 is not copied as a duplicate file.
5. Historical FAS-010 AI Council becomes canonical FAS-011.
6. Historical FAS-011–036 shift by one to canonical FAS-012–037.
7. A historical identifier is provenance, not an alias that can be used in new
   code or schemas.
8. Current documents may cite a historical source only through the explicit
   mapping in this roadmap.

## 3. Status vocabulary

- **Implemented:** Present in production code/specifications on `main`.
- **Next:** First dependency-correct specification to implement.
- **Baseline:** Required for or directly supporting the local v1.0 release.
- **Baseline foundation:** Architectural contract required before dependent
  baseline work, even if its full feature surface ships later.
- **Future-gated:** Accepted architecture deliberately excluded from v1.0.
- **Review later:** Accepted draft that must receive a capability/production
  review before implementation.

## 4. Canonical FAS ledger

| Canonical | Production title | Status | v1 relevance | Historical source |
| --- | --- | --- | --- | --- |
| FAS-001 | Constitutional Governance Foundation | Implemented | Baseline | Historical FAS-001 |
| FAS-002 | Stable Kernel Architecture | Implemented | Baseline | Historical FAS-002 |
| FAS-003 | Capability Framework | Implemented | Baseline | Historical FAS-003 |
| FAS-004 | Mission Framework | Implemented | Baseline | Historical FAS-004 |
| FAS-005 | Forge Executive | Implemented | Baseline | Historical FAS-005 |
| FAS-006 | Forge Event System | Implemented | Baseline | Historical FAS-006 |
| FAS-007 | Decision Ledger and Evidence Architecture | Implemented | Baseline | Historical FAS-007 |
| FAS-008 | Policy Decision and Authorization Engine | Implemented | Baseline | Reconciles historical FAS-009 authority rules |
| FAS-009 | Policy Bundle Governance | Implemented | Baseline | Extends historical FAS-009 policy governance |
| FAS-010 | Trust Framework, Identity, Signing, and Sentinel | Implemented | Baseline foundation | Historical FAS-008 |
| FAS-011 | AI Council Architecture | Planned | Future-gated | Historical FAS-010 |
| FAS-012 | User Interaction, Suggestions, and Attention | Implemented | Baseline | Historical FAS-011 |
| FAS-013 | Knowledge Core and Operational Memory | Implemented | Baseline foundation | Historical FAS-012 |
| FAS-014 | Plugin SDK and Extension Architecture | Implemented | Baseline | Historical FAS-013 |
| FAS-015 | Mission Scheduling and Priority | Implemented | Baseline | Historical FAS-014 |
| FAS-016 | Distributed FORGE Nodes and Shared Ecosystem | Planned | Future-gated | Historical FAS-015 |
| FAS-017 | Shared Evidence Network Governance | Planned | Future-gated | Historical FAS-016 |
| FAS-018 | Verification, Validation, and Assurance | Implemented | Baseline | Historical FAS-017 |
| FAS-019 | Object System and Digital Twin | Implemented | Baseline | Historical FAS-018 |
| FAS-020 | User Identity, Onboarding, and Experience Selection | Implemented | Baseline | Historical FAS-019 |
| FAS-021 | Configuration, Profiles, and Change Management | Planned | Baseline | Historical FAS-020 |
| FAS-022 | Runtime, Execution Context, and Resources | Planned | Baseline | Historical FAS-021 |
| FAS-023 | Health, Diagnostics, and Recovery | Planned | Baseline | Historical FAS-022 |
| FAS-024 | Local Interface, API, and Accessibility | Planned | Baseline | Historical FAS-023 |
| FAS-025 | Testing, Simulation, and Release Assurance | Planned | Baseline | Historical FAS-024 |
| FAS-026 | Local Data Ownership, Persistence, Backup, and Recovery | Planned | Baseline | Historical FAS-025 |
| FAS-027 | Executive Lifecycle and Service Management | Planned | Baseline | Historical FAS-026 |
| FAS-028 | Hardware Interface and Transport | Planned | Baseline | Historical FAS-027 |
| FAS-029 | Capability Design Review: Motion and Positioning | Review later | Baseline review | Historical FAS-028 |
| FAS-030 | Capability Design Review: Thermal Management | Review later | Baseline review | Historical FAS-029 |
| FAS-031 | Capability Design Review: Material Handling and Extrusion | Review later | Baseline review | Historical FAS-030 |
| FAS-032 | Capability Design Review: Vision and Observation | Review later | Optional baseline | Historical FAS-031 |
| FAS-033 | Manufacturing Artifact, G-code, and Preflight | Review later | Baseline | Historical FAS-032 |
| FAS-034 | Print Execution and Job Lifecycle | Review later | Baseline | Historical FAS-033 |
| FAS-035 | Capability Design Review: Environment, Power, and Safety Sensors | Review later | Optional baseline | Historical FAS-034 |
| FAS-036 | Software Updates, Compatibility, and Rollback | Review later | Baseline | Historical FAS-035 |
| FAS-037 | FORGE v1.0 Baseline Release Scope | Review later | Release gate | Historical FAS-036 |

## 5. Dependency-correct delivery sequence

### Phase A — Close production trust boundaries

1. **FAS-010 — Trust Framework, Identity, Signing, and Sentinel**
   - Required by current FAS-008/FAS-009 production boundaries.
   - Defines key identity, signature verification, rotation, revocation,
     attestations, approval verification, software integrity, and Sentinel's
     constrained enforcement authority.
2. **FAS-012 — User Interaction, Suggestions, and Attention**
   - Can proceed without implementing the future AI Council.
   - Establishes AI-free operation and the `You decide. Forge follows.` rule.
3. **FAS-013 — Knowledge Core and Operational Memory**
   - Establishes evidence-backed local memory and user correction authority.
4. **FAS-018 — Verification, Validation, and Assurance**
   - Consolidates assurance classes and the threshold between hypothesis,
     recommendation, authorization, and measured outcome.

FAS-011 remains specified but future-gated. Baseline code may define an
AI-provider-neutral evidence interface without shipping Council operation.

### Phase B — Build the local extensible platform

1. FAS-014 Plugin SDK and no-code custom hardware.
2. FAS-015 local Mission scheduling and priority.
3. FAS-019 Object System and Operational Twin v0.1.
4. FAS-020 local identity/onboarding modes.
5. FAS-021 configuration and rollback.
6. FAS-022 runtime contexts, locks, and leases.
7. FAS-023 health and narrow recovery.
8. FAS-024 local interfaces and accessibility.
9. FAS-025 testing and release assurance.
10. FAS-026 local persistence, backup, and restore.
11. FAS-027 startup, service lifecycle, and shutdown.
12. FAS-028 replaceable hardware transport with Moonraker/Klipper as the first
    reference provider.

### Phase C — Review and implement manufacturing capabilities

Review in dependency order before production code:

1. FAS-029 Motion and Positioning.
2. FAS-030 Thermal Management.
3. FAS-031 Material Handling and Extrusion.
4. FAS-032 Vision and Observation.
5. FAS-035 Environment, Power, and Safety Sensors.
6. FAS-033 Manufacturing Artifact, G-code, and Preflight.
7. FAS-034 Print Execution and Job Lifecycle.
8. FAS-036 Updates, Compatibility, and Rollback.
9. FAS-037 v1.0 release-scope review and release gate.

### Phase D — Future-gated ecosystem and autonomy

- FAS-011 AI Council operation.
- FAS-016 distributed nodes and shared compute.
- FAS-017 shared evidence network.
- Assisted, supervised, and A5 delegated autonomy release surfaces.
- Advanced simulation, autonomous slicing/file optimization, and AI-generated
  toolpaths.

These remain architecturally recognized but are not required to make the local
v1.0 product useful.

## 6. Dependency translation policy

When porting a historical document:

- Translate historical FAS-008 references to canonical FAS-010 when they mean
  Trust/Sentinel.
- Translate historical FAS-009 references to canonical FAS-008 and/or FAS-009
  according to whether they mean authorization evaluation or policy lifecycle.
- Translate historical FAS-010 references to canonical FAS-011.
- Translate historical FAS-011–036 references by adding one.
- Inspect the meaning rather than mechanically replacing all identifiers.
- Replace `Draft 1` with the current production status only after a fresh
  architecture review and executable validation.

## 7. Acceptance criteria

This reconciliation is complete when:

1. Every historical FAS-001–036 maps exactly once.
2. Every canonical FAS identifier is unique.
3. Current production FAS-001–009 retain their meanings and history.
4. No historical draft is copied into production under a conflicting number.
5. Future work uses canonical identifiers only.
6. Phase A is implemented: FAS-010, FAS-012, FAS-013, and FAS-018.
   FAS-014 and FAS-015 are implemented; FAS-019 is the next local-platform
   specification because FAS-016 and FAS-017 remain future-gated. FAS-019 is
   implemented; FAS-020 is implemented and FAS-021 is next.

## Decisions needed

None. This roadmap preserves previously approved concepts and resolves
identifier collisions without changing product authority or v1 scope.
