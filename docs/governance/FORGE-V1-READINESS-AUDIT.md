# FORGE v1.0 Repository Readiness Audit

Status: Current verified baseline
Audit date: 2026-07-27
Audited commit: `a62431a`

## Verdict

The repository is a coherent and tested **reference-contract baseline** aligned
with the FORGE Constitution. It is not yet a complete v1.0 application and must
not be described as release-ready.

The implemented FAS entries provide executable domain contracts, schemas,
examples, and tests. They do not yet provide the complete desktop application,
local persistence, service lifecycle, production hardware provider, integrated
slicer worker, four-click interface, or controlled print lifecycle required for
v1.0.

FAS-026 now adds the tested local data and recovery reference contract. FAS-027
adds the tested service lifecycle reference contract. FAS-028 adds the tested
hardware transport reference contract. FAS-029 and FAS-030 add reviewed
motion, thermal, material, optional vision, artifact preflight, and job
lifecycle, optional safety-sensor, and update/rollback contracts. The
remaining persistence work is filesystem durability, encryption, crash-atomic
transactions, and integration with the application lifecycle.

## Sources reviewed

- the root FORGE Constitution and FAS-001;
- all current files under `docs`, `schemas`, `examples`, `src`, and `tests`;
- the production decision register, roadmap, reconciliation map, and
  conversation provenance;
- the historical FAS007-FAS036 Codex thread;
- the current Continue uploading fas-009 Codex thread;
- the approved OrcaSlicer integration and licensing decisions; and
- the Git history through the audited commit.

Historical architecture informs intent. The current production repository,
canonical numbering, approved decisions, and Constitution remain authoritative.

## Verified integrity

- Git working state was clean at audit start and matched `origin/main`.
- `git fsck --full --strict` reported no object corruption.
- No tracked file was missing and no tracked symbolic link was present.
- The current full validation passed 609 tests, skipped 1 platform-dependent
  test, and passed 188 subtests.
- Python source and tests compiled successfully.
- Installed Python dependencies reported no broken requirements.
- A clean isolated wheel build produced `forge-0.25.0-py3-none-any.whl`.
- FAS-037 is implemented; the reconciliation map now identifies the final
  human RELEASE-GATE rather than another FAS specification.
- FAS-011, FAS-016, and FAS-017 are intentionally future-gated rather than
  accidentally missing.
- The optional non-free Bambu networking plugin is excluded from the trusted
  baseline.

## Folder assessment

| Location | Purpose | Audit result |
| --- | --- | --- |
| repository root | authority, orientation, packaging, license state | Corrected: Constitution restored; package notes moved out |
| `.github/workflows` | repeatable repository validation | Added; required before v1 |
| `docs/architecture` | normative FAS and ADR documents | Correct for current implemented/approved set |
| `docs/governance` | decisions, history, roadmap, worklists, audits | Correct after stale-next-step correction |
| `docs/compliance` | upstream and license evidence | Correct but Gate 1 incomplete |
| `docs/releases` | historical per-FAS implementation notes | Correct home for non-normative package notes |
| `schemas/fas` | versioned data contracts | Correct for current reference components |
| `examples/fas` | valid representative contract instances | Correct and test-covered |
| `src/forge/fas` | reference implementations | Correct; not yet a complete application runtime |
| `tests/fas` | behavioral, schema, and governance verification | Correct; CI now repeats the documented suite and fail-closed Gate 1 check |

## Constitutional alignment

### Confirmed

- **Users decide:** authorization, Mission, Runtime, and interface contracts do
  not infer authority from confidence, simulation, slicing, or events.
- **Evidence first:** decision, verification, trust, health, and test contracts
  preserve evidence and limitations.
- **Hardware freedom:** capabilities and plugins represent custom, unknown, and
  off-brand hardware without kernel enumeration.
- **Local first:** onboarding, knowledge, interface, and future persistence
  direction do not require cloud or AI.
- **Explainability:** denials, limitations, unknowns, health, suggestions, and
  recovery paths carry human-readable reasons.
- **Safety boundaries:** Executive authorization remains separate from drivers,
  providers, twin output, and simulation.
- **Open ecosystem:** OrcaSlicer is a governed capability; the non-free
  networking plugin is not a trusted dependency.

### Not yet proven for v1

- complete plain-language documentation for every eventual application service;
- a usable local application and accessible four-click workflow;
- persistent local data, backup, restore, migration, and recovery;
- production lifecycle startup, shutdown, crash recovery, and packaging;
- real provider integration and hardware-in-the-loop evidence;
- STEP/3MF quarantine and the Orca-derived slicing worker;
- end-to-end preflight, final **Yes, Print**, upload, start, monitoring, and
  measured completion;
- signed releases, SBOM, corresponding source, installer, rollback, and support
  documentation.

## Blocking sequence to v1.0

1. **Licensing Gate 1:** archive and hash pinned Orca source/license material,
   complete the file-level inventory, select the exact SPDX expression, and add
   the final license/notices/SBOM/source-publication package.
2. **FAS-026:** reference contract implemented; finish filesystem durability,
   encryption, crash-atomic transactions, and application integration.
3. **FAS-027:** reference contract implemented; finish process supervision,
   crash recovery, and application integration.
4. **FAS-028:** reference contract implemented; finish provider adapters and
   physical dispatch integration.
5. **FAS-029:** reference review implemented; finish calibration and
   hardware-in-the-loop evidence for motion providers.
6. **FAS-030:** reference review implemented; finish independent thermal
   cutoffs and runaway testing.
7. **FAS-031:** reference review implemented; finish material calibration,
   load testing, and jam-recovery evidence.
8. **FAS-032:** optional review implemented; keep vision non-blocking unless
   the release claims vision capabilities.
9. **FAS-033:** reference preflight implemented; finish integrated slicing and
   complete artifact validation.
10. **FAS-034:** reference lifecycle implemented; finish upload/start and
    monitoring integration.
11. **FAS-035:** optional safety review implemented; keep it non-blocking unless
    the release claims those capabilities.
12. **FAS-036:** reference update and rollback contract implemented; finish
    packaging and compatibility integration.
13. **Slicer Gates 2 and 3:** reproduce the pinned upstream build, prove the
   worker boundary, and specify STEP/3MF, Manufacturing Intent, provenance,
   production/twin, and four-click state contracts.
14. **Slicer Gates 4 and 5:** complete integrated slicing, the accessible
   four-click UI, live checks, controlled upload/start, monitoring, and outcome
   recording.
15. **Slicer Gate 6:** complete security, reproducibility, fault,
   accessibility, and hardware-in-the-loop assurance.
16. **FAS-037:** reference release-scope gate implemented; perform the final
   constitutional, licensing, safety, documentation, installation, recovery,
   and release decision.

FAS-032 vision and FAS-035 optional sensor families are not v1 blockers unless
the release claims their capabilities. AI Council operation, distributed
nodes, shared evidence, autonomous slicing decisions, AI-generated toolpaths,
and A5 autonomy remain future-gated.

## Immediate next work

Follow the ordered prerequisite checklist in
`docs/governance/FORGE-V1-NEXT-STEP-PREREQUISITES.md`, beginning with Licensing
Gate 1, provenance decisions, and qualified legal review. Contract-only Slicer
Gate 3 work may proceed without importing Orca source, but no Orca-derived code
or public integrated distribution may bypass the licensing gate.

## Decisions or attention

The next completion packet must resolve Gate 1 licensing/provenance decisions
and obtain qualified legal review before any Orca source import or public
integrated distribution. This audit preserves the already approved v1 scope and
authority model.
