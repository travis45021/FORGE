# ADR-001: OrcaSlicer-Derived Slicing Foundation

Status: Approved  
Effective date: 2026-07-26  
Scope: Cross-cutting architecture and release prerequisite

## Context

FORGE needs an integrated slicing capability without becoming only a slicer.
It must preserve user authority, hardware neutrality, local-first operation,
explainability, and the Executive-controlled path to physical work.

OrcaSlicer supplies a mature open-source slicing foundation. FORGE remains the
system that owns Objects, Builder flows, Missions, authority, verification,
runtime control, the Operational Twin, and learning. The slicer is a governed
capability inside that system.

## Decision

### 1. Upstream and engine structure

- OrcaSlicer is the approved upstream slicing foundation.
- FORGE will maintain one Orca-derived engine codebase.
- That engine may run in two isolated execution contexts:
  - the **production context** creates the candidate manufacturing artifact;
  - the **twin context** creates independent, advisory toolpath evidence for
    comparison and verification.
- The two contexts must not become divergent product forks.
- Neither context may authorize a Mission, command hardware, upload to a
  printer, or start a print.
- Only the FORGE Executive and Runtime may pass an authorized artifact to a
  capability provider through the controlled Mission path.

### 2. Initial input boundary

- The first integrated design inputs are STEP and 3MF.
- Full F3D project support is deferred.
- Existing G-code remains an imported manufacturing artifact governed by
  preflight; it is not treated as a design input that must be sliced.
- Additional CAD formats require a later explicit capability and licensing
  review.

### 3. Mandatory four-click v1 workflow

The baseline user journey is:

1. Add a STEP or 3MF file.
2. Confirm the context and settings inferred or selected by FORGE.
3. Create the verified Print Mission.
4. After live printer checks pass, choose **Yes, Print**. Only after that
   confirmation may FORGE perform controlled upload or start.

The fourth confirmation is mandatory for every v1 user. A future bypass
structure may be represented in policy, but it must remain disabled and must
not be exposed as a usable authority path in v1.

This decision permits user-directed automatic slicing inside the four-click
workflow. It does not enable autonomous file optimization, AI-generated
toolpaths, autonomous print start, or A5 delegated autonomy.

### 4. Licensing direction

- The integrated FORGE application adopts GNU AGPL version 3 as its approved
  licensing direction.
- The exact project-wide SPDX expression, including `-only` versus
  `-or-later`, will be selected only after a file-level provenance and
  compatibility audit.
- Existing copyright notices, upstream license notices, asset licenses,
  translations, profiles, calibration content, and dependency obligations must
  be preserved.
- Earlier FORGE bootstrap code reused from the MIT-licensed historical
  checkout must preserve its MIT copyright and permission notice.
- A public binary or hosted release containing Orca-derived code is blocked
  until the source, notice, and corresponding-source obligations have passed
  the release compliance gate.
- The optional non-free Bambu networking plugin is excluded from FORGE's
  trusted baseline.

The software license does not claim ownership of user data. User design files,
profiles, local knowledge, evidence, and produced artifacts remain user-owned
unless the user separately chooses to share them under explicit terms.

### 5. Integration boundaries

- Slicer profiles are derived ephemerally from verified FORGE Objects,
  capabilities, configuration, material, process, and Mission intent.
- An Orca-native profile must not become a second authoritative hardware
  database.
- Every output records input digests, engine version, profile digest, execution
  context, warnings, and reproducibility information.
- Production and twin results remain distinguishable evidence.
- Differences between the contexts are explained and evaluated by FORGE
  preflight; twin output is never authority by itself.
- Direct printer discovery, vendor cloud access, telemetry, upload, and start
  paths in the upstream application must be disabled or isolated from the
  trusted slicing worker.

## Consequences

- FORGE gains a mature slicer foundation while keeping its broader platform
  identity and constitutional authority model.
- Upstream integration begins with licensing and provenance gates, not source
  import.
- The initial implementation is narrower than OrcaSlicer's full desktop
  feature surface.
- Upstream synchronization, reproducible builds, notices, and source
  publication become recurring release responsibilities.
- FAS-028 is the next canonical specification. This ADR is a cross-cutting
  prerequisite and does not consume or renumber a FAS identifier.

## Non-goals

- Two separately modified Orca forks.
- Direct hardware authority inside a slicer worker.
- A Bambu cloud or non-free networking dependency.
- Full F3D architecture in the initial release.
- Autonomous print start or removal of the final v1 confirmation.
