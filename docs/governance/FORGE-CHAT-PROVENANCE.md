# FORGE Conversation Provenance Index

Status: Living historical index  
Last consolidated: 2026-07-25  
Repository: `travis45021/FORGE`

## Purpose

This index records the known FORGE-related conversations that shaped the
production architecture. It preserves where decisions came from while keeping
the repository, Constitution, and approved specifications authoritative.

## Indexed conversations

### 1. Extruder Setting Issues

- Thread ID: `6a610531-55f8-83ea-ab80-d8d821933b7d`
- Kind: ChatGPT
- Historical role: Origin of the K1 Max Performance Edition effort.
- Important context:
  - Initial reference hardware was a 2025 Creality K1 Max with DXC Slim
    extruder, Unicorn hotend, hardened 0.4 mm nozzle, Mainsail/Moonraker, and a
    strong PETG focus.
  - Proposed a modular macro/configuration repository, staged testing,
    diagnostics, backups, and avoiding invented machine values.
- Authority note: Printer-specific macro proposals are historical reference
  material, not current FORGE platform contracts.

### 2. New chat — K1 Max Performance Edition macros

- Thread ID: `6a624d21-04c4-83ea-82a2-9b60ef0b0ddc`
- Kind: ChatGPT
- Historical role: Follow-on packaging plan for the K1 Max macro overlay.
- Important context:
  - Mainsail was confirmed as the primary interface.
  - Proposed a community-quality, documented, modular macro pack.
- Authority note: Superseded as the main product direction when FORGE became a
  printer-neutral manufacturing platform. Retain as reference-provider input.

### 3. Forge executive specification

- Thread ID: `6a627057-b6bc-83ea-9f49-6d650a3d8475`
- Kind: ChatGPT
- Historical role: Executive-level product architecture and program planning.
- Important context:
  - Defined FORGE as an evidence-driven, local-first manufacturing intelligence
    platform rather than a slicer, host, chatbot, or dashboard.
  - Established user authority, Preview → Review → Apply → Rollback, earned
    automation, local-first operation, modularity, open interfaces,
    reproducibility, AI-provider independence, and inspectability.
  - Proposed phased construction, subsystem ownership, engineering gates,
    definition of done, architecture-drift protection, and a multi-horizon
    roadmap.
  - Assigned product direction and final approval to the founder; architecture
    and engineering recommendations to the technical role.
- Authority note: Contains many exploratory organizational names. Product
  principles remain useful; current repository names and contracts win.

### 4. Code Architecture Plan

- Thread ID: `6a62de3b-0838-83ea-900a-d920578d7215`
- Kind: ChatGPT
- Historical role: Constitution and FAS-001 through FAS-006 design source.
- Important context:
  - Elevated the Forge Constitution to the project's highest authority.
  - Established capability-first, hardware-neutral, stable-kernel architecture.
  - Defined Missions, the non-AI Executive, the event system, user/developer
    error explanations, Sentinel boundaries, and open custom-hardware support.
  - Established the response preference to end major production updates with
    decisions requiring user attention.
- Authority note: The current repository contains reconstructed production
  versions of FAS-001 through FAS-006. Those files supersede chat drafts.

### 5. FAS007-FAS036

- Thread ID: `019f961d-18c9-7573-b351-21abf69c6c3d`
- Kind: Codex
- Historical role: Complete long-form architecture ledger and early executable
  scaffold.
- Important context:
  - Created historical FAS-007 through FAS-036, then added historical FAS-001
    through FAS-006, a Constitution, and a ledger.
  - Recorded approvals covering decision evidence, trust/Sentinel, authority,
    AI Council, suggestions, knowledge, plugins, scheduling, distributed nodes,
    verification, autonomy classes, object/twin architecture, onboarding,
    configuration, runtime, recovery, interfaces, testing, local data,
    hardware transport, motion, thermal, materials, vision, G-code, print
    lifecycle, sensors, updates, and v1.0 scope.
  - Built and validated an earlier Python bootstrap with tests, packaging,
    linting, formatting, typing, and Python 3.14 verification.
- Authority note: This thread used an older FAS numbering scheme. In particular,
  historical FAS-009 meant Policy/Authority Governance and historical FAS-010
  meant AI Council. Current production FAS-008 is the Authorization Engine and
  current production FAS-009 is Policy Bundle Governance. Preserve concepts,
  not conflicting historical file numbers.

### 6. Forge Production FAS008

- Thread ID: `6a64f544-cc88-83ea-baef-8b6071b35ef8`
- Kind: ChatGPT
- Historical role: Production transition from FAS-007 to FAS-008.
- Important context:
  - Reported the production FAS-007 Decision Ledger/Evidence Architecture as
    complete.
  - Declared FAS-008 Policy Decision and Authorization Engine as the next
    production milestone.

### 7. Connect FORGE Repository

- Thread ID: `6a64fd1e-4940-83ea-8253-71f976e86da9`
- Kind: ChatGPT
- Historical role: GitHub connection troubleshooting.
- Important context:
  - Established the official repository target as `travis45021/FORGE`.
  - Contains no binding architecture decision.

### 8. Connect GitHub Repository

- Thread ID: `6a6502ad-3f64-83ea-b9a7-4bd137e2a071`
- Kind: ChatGPT
- Historical role: Production reconstruction, validation, and publication.
- Important context:
  - Completed and uploaded production FAS-007 and FAS-008.
  - Reconstructed production FAS-001 through FAS-006.
  - Added the optional strict JSON Schema validator.
  - Renamed project artifacts from `K1MAX-Forge-*` to `FORGE-*`.
  - Completed the validated FAS-001–009 package.
- Repository milestones:
  - `abbce255dee4e530825723f455ae98a923f0bc0f` — validated FAS-001–008
    foundation.
  - FAS-009 package SHA-256:
    `918709026d5df9995b58752fdf12576ec585489e1fbb5917e8e4a729b9bb6008`.

### 9. Continue uploading fas-009

- Thread ID: `019f9b04-88ea-7bc0-9cd4-1b6222651887`
- Kind: Codex
- Historical role: Current production publication and provenance consolidation.
- Important context:
  - Uploaded FAS-009 without overwriting prior repository history.
  - Verified commit
    `4966cbc1d84a30707c821b2d559f8f20fb842237`.
  - Initiated this conversation/decision consolidation.

## Excluded or contextual-only conversations

General print-quality chats (adhesion, PETG first layers, support issues,
G-code troubleshooting, cameras, and unrelated device support) may contain
useful evidence for future printer diagnostics, but they do not define FORGE
production architecture unless a later approved specification explicitly adopts
their findings.

## How future work should cite a conversation

Use the conversation title and exact thread ID, for example:

`FAS007-FAS036 (thread 019f961d-18c9-7573-b351-21abf69c6c3d)`

Then cite the active repository document or decision-register entry that adopted
the idea. Conversation provenance explains origin; it should not replace a
current contract.

