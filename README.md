# FORGE

[The FORGE Constitution](CONSTITUTION.md) is the highest project authority.
Every specification, implementation, integration, and release must conform to
it.

FORGE is an open, capability-based 3D-printing control and assurance platform.
It is designed to support known and user-defined printers, components,
materials, accessories, and automation without redesigning the core for every
new device.

## Approved slicer foundation

FORGE will integrate an OrcaSlicer-derived engine as a governed capability, not
as a separate authority or a replacement for the FORGE platform. One maintained
engine will run in isolated production and twin contexts. The first design
inputs are STEP and 3MF; full F3D project support is deferred.

The v1 print path requires four user actions. The final **Yes, Print** occurs
after live printer checks and before controlled upload or start, and cannot be
bypassed in v1. GNU AGPL version 3 is the approved licensing direction, but
Orca source import and public integrated distribution remain blocked until the
file-level licensing and provenance audit is complete.

See `docs/architecture/ADR-001-orcaslicer-slicing-foundation.md`,
`docs/governance/FORGE-SLICER-LICENSING-INTEGRATION-TODO.md`, and
`LICENSE-STATUS.md`.

The current tested reference-contract baseline contains:

- **FAS-001:** Constitutional Governance Foundation
- **FAS-002:** Stable Kernel Architecture
- **FAS-003:** Capability Framework
- **FAS-004:** Mission Framework
- **FAS-005:** Forge Executive
- **FAS-006:** Forge Event System
- **FAS-007:** Decision Ledger and Evidence Architecture
- **FAS-008:** Policy Decision and Authorization Engine
- **FAS-009:** Policy Bundle Governance
- **FAS-010:** Trust Framework, Identity, Signing, and Sentinel
- **FAS-011:** AI Council Architecture (future-gated)
- **FAS-012:** User Interaction, Suggestions, and Attention
- **FAS-013:** Knowledge Core and Operational Memory
- **FAS-014:** Plugin SDK and Extension Architecture
- **FAS-015:** Mission Scheduling and Priority
- **FAS-018:** Verification, Validation, and Assurance
- **FAS-019:** Object System and Digital Twin
- **FAS-020:** User Identity, Onboarding, and Experience Selection
- **FAS-021:** Configuration, Profiles, and Change Management
- **FAS-022:** Runtime, Execution Context, and Resources
- **FAS-023:** Health, Diagnostics, and Recovery
- **FAS-024:** Local Interface, API, and Accessibility
- **FAS-025:** Testing, Simulation, and Release Assurance
- **FAS-026:** Local Data Ownership, Persistence, Backup, and Recovery
- **FAS-027:** Executive Lifecycle and Service Management
- **FAS-028:** Hardware Interface and Transport
- **FAS-029:** Capability Design Review: Motion and Positioning
- **FAS-030:** Capability Design Review: Thermal Management

FAS-001 through FAS-006 were reconstructed from approved project decisions
and the dependency contracts already published by FAS-007 and FAS-008. Each
specification identifies its reconstruction status.

FAS-008 includes a deterministic reference evaluator under
`src/forge/fas/authorization.py`. It is an authorization component, not a
printer-control service.

FAS-009 adds an immutable, content-addressed bundle registry and governed
activation/rollback reference component under
`src/forge/fas/policy_bundles.py`.

FAS-010 adds deterministic trust verification, immutable key lineage,
revocation, signed approvals, and a non-authoritative Sentinel evidence
boundary under `src/forge/fas/trust.py`.

FAS-011 is architecturally recognized but deliberately future-gated.

FAS-012 adds AI-free and suggestion-free defaults, attention budgets,
deduplication, dismissal, quiet hours, and strict separation between
interaction preferences and automation authority under
`src/forge/fas/interactions.py`.

FAS-013 adds evidence-backed local knowledge, explicit uncertainty, user
correction and supersession, dependency invalidation, advisory shared
knowledge, and deterministic export under `src/forge/fas/knowledge.py`.

FAS-014 adds capability-bound plugin manifests, scoped permissions, validation
and activation gates, quarantine, and a no-code provisional custom-hardware
path under `src/forge/fas/plugins.py`.

FAS-015 adds deterministic scheduling for authorized Missions, resource and
condition waits, safe preemption, bounded retries, fairness, and AI-free local
operation under `src/forge/fas/scheduler.py`.

FAS-018 adds contextual Verification Packets, scaled A0-A4 gates, explicit
claim states, separate authority verification, measured outcomes, and a
future-gated A5 boundary under `src/forge/fas/assurance.py`.

FAS-019 adds a typed, versioned object graph and the opt-in Digital Twin v0.1
Operational Twin under `src/forge/fas/objects.py`.

FAS-020 adds local identity without an account, conservative v1 experience
profiles, composable settings, explicit sharing consent, and separate authority
changes under `src/forge/fas/onboarding.py`.

FAS-022 adds recorded Execution Contexts, expiring resource leases, guarded
provider dispatch, controlled state transitions, and safe restart assessment
under `src/forge/fas/runtime.py`.

FAS-023 adds evidence-backed multi-state health, freshness evaluation,
dependency impact, bounded low-risk recovery, retry suppression, and verified
recovery outcomes under `src/forge/fas/health.py`.

FAS-024 adds a local-first, versioned Interface Gateway, shared Executive request
path, explainable approvals, structured errors, observational subscriptions,
and accessibility contracts under `src/forge/fas/interfaces.py`.

FAS-025 adds layered reproducible testing, honestly labeled simulation,
bounded hardware-in-the-loop validation, and evidence-based release gating
under the reference testing service.

FAS-026 adds local ownership, provenance-backed data records, digest-verified
backup manifests, secret separation, portable export, conflict-preserving
restore modes, and migration planning under the persistence reference service.
Restore cannot replay commands or resume physical work.

This reference baseline is not yet a complete v1 application. The current
release gaps and dependency-correct path are recorded in
`docs/governance/FORGE-V1-READINESS-AUDIT.md`.

## Validation

Install the optional strict Draft 2020-12 schema validator:

```bash
python -m pip install -e ".[validation]"
```

Run the complete FAS test suite:

```bash
python -m unittest discover -s tests/fas -p "test_*.py" -v
```

The same suite, compilation check, dependency-health check, and wheel build run
in `.github/workflows/ci.yml`.

The validator is intentionally optional: FORGE runtime components use only the
Python standard library, while validation and development environments can
enable strict schema and format checks through the `validation` extra.
