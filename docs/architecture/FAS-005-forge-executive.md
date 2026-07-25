# FAS-005 — Forge Executive

Status: Reconstructed production specification  
Version: 1.0.0  
Depends on: FAS-001 through FAS-004  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

The Forge Executive is the authoritative decision and orchestration engine. It
coordinates missions, capabilities, policy, AI, Sentinel, resources, conflict
resolution, and recovery. It does not directly control hardware or generate
motion commands.

Every significant action must be authorized, explainable, safe, observable,
recoverable, auditable, and constitutionally compliant.

## 2. Decision pipeline

1. Receive Request
2. Validate Mission
3. Verify Authority
4. Gather Evidence
5. Evaluate Policies
6. Resolve Capabilities
7. Consult AI, if required
8. Perform Risk Analysis
9. Select Action
10. Record Decision
11. Execute through an authenticated capability provider
12. Observe Outcome
13. Update Mission

AI produces attributable proposals. Confidence does not grant authority. The
Executive consumes an authorization result and never converts `challenge` or
`deny` into execution.

## 3. Orchestration rules

- decisions and execution are separate phases;
- approved actions are bounded by their effective parameters;
- Sentinel and integrity blocks are terminal;
- capability conflicts are resolved deterministically and visibly;
- retries require idempotency keys and cannot broaden parameters;
- observed results are reconciled with approved actions;
- recovery is itself a mission action subject to policy.

## 4. Acceptance criteria

The reference coordinator produces a deterministic ordered pipeline, halts
before execution on any failed gate, emits a bounded execution request only
after approval, and records outcome and mission state separately.
