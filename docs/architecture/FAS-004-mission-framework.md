# FAS-004 — Forge Mission Framework

Status: Reconstructed production specification  
Version: 1.0.0  
Depends on: FAS-001; FAS-002; FAS-003  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

A Mission is a structured, evidence-driven objective executed by the Forge
Executive through capabilities while respecting policy, safety, delegated
authority, and user intent.

## 2. Mission definition

A mission contains its objective, requirements, constraints, context,
evidence, dependencies, capability requirements, plan, risk assessment,
approval requirements, execution steps, monitoring rules, recovery strategy,
completion criteria, and report requirements. Plans request capability
operations; they do not embed driver-specific direct control.

## 3. Lifecycle

The principal path is:

`created → validated → planned → waiting → approved → executing → monitoring →
completed → verified → archived`

Alternate states are `paused`, `cancelled`, `failed`, `aborted`, `recovering`,
and `suspended`. Every transition requires an allowed transition, actor,
reason, correlation identifier, and event. Material transitions are recorded
in the Decision Ledger.

## 4. Templates and replay

Templates may inherit from versioned parents, but a created mission snapshots
the resolved template. Replay creates a new mission linked to the original and
reuses no expired approvals or mutable authority. Historical missions never
change when templates change.

## 5. Acceptance criteria

- mission definitions are portable across compatible providers;
- invalid transitions are rejected;
- execution cannot begin before validation, planning, and approval;
- cancellation and recovery are explicit states;
- completion and verification are distinct;
- replay preserves provenance without reusing authority.
