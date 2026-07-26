# FAS-001 — Forge Constitutional Governance Foundation

Status: Reconstructed production specification  
Version: 1.0.0  
Depends on: None  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

FAS-001 establishes the authority, invariants, and change-governance model for
FORGE. The Constitution is the highest project authority. The complete
normative text is `../../CONSTITUTION.md`. The authority order is:

1. Constitution
2. FAS specifications
3. standards
4. public APIs and contracts
5. source code
6. plugins and integrations

Lower layers may implement or narrow higher-layer rules; they may not silently
override them.

## 2. Constitutional invariants

- Users decide; automation assists or follows.
- Safety, security, privacy, accessibility, and user control are design inputs.
- The kernel is hardware-neutral and unknown hardware remains representable.
- Contracts precede implementations.
- Significant decisions are explainable, observable, recoverable, and auditable.
- Open documentation and interoperability are defaults.
- Authority is explicit, scoped, revocable, and never inferred from confidence.
- Sentinel may block unsafe or untrusted action but may not broaden authority.
- Stable core contracts evolve compatibly; extensions do not require core redesign.

## 3. Governance roles

The end user controls user-owned intent and data within policy. Forge Admin
holds explicit ARL 5 administrative authority but cannot bypass Sentinel. The
Forge Architect owns architectural intent and interface invariants. The AI
Council advises and records dissent without implicit execution authority.
Sentinel enforces purpose-limited safety and security blocks.

## 4. Conformance and change

Every normative artifact declares identity, version, owner, dependencies, and
status. Breaking changes require a new major version, migration plan, impact
assessment, validation evidence, and an authorized decision record. Emergency
protective changes may block execution immediately, but permanent adoption
still follows review and append-only decision recording.

## 5. Acceptance criteria

- authority order is machine- and human-readable;
- roles do not gain ambient machine authority;
- incompatible lower-layer behavior fails validation;
- an unknown printer or component can enter through capability contracts;
- governance changes are attributable, versioned, and reviewable.

## 6. Reconstruction note

The hierarchy and invariants are recovered project decisions. This document
formalizes their minimum production contract so FAS-002 through FAS-008 share a
single authority model.
