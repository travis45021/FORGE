# FAS-003 — Forge Capability Framework

Status: Reconstructed production specification  
Version: 1.0.0  
Depends on: FAS-001; FAS-002  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

FAS-003 defines capabilities as atomic, discoverable, versioned behavior.
Capabilities let FORGE support known and unknown hardware without closed
printer, accessory, or manufacturer enumerations.

## 2. Contract

A capability contract declares:

- stable namespaced identity and semantic version;
- provider identity and compatible contract version;
- atomic operations with input, output, timeout, idempotency, and side effects;
- state machine and allowed transitions;
- health, evidence, safety, error, and configuration contracts;
- required permissions and dependencies;
- lifecycle hooks and conformance tests.

Capabilities describe behavior such as `forge.motion.axis`, `forge.thermal.zone`
or `user.material.conditioning`; they do not encode a product allowlist.

## 3. Resolution

Consumers request capability requirements, not providers. The registry filters
compatible versions, required operations, health, trust, permissions, safety
constraints, and current availability. Selection is deterministic. No match is
an explicit unresolved requirement, never a guessed substitution.

## 4. Invocation rules

The caller supplies operation, validated inputs, correlation and idempotency
identifiers, authority context, and deadline. The provider returns normalized
success or error evidence. Mutable operations require FAS authorization and
produce FAS-006 events.

## 5. Acceptance criteria

- arbitrary namespaced capabilities validate;
- required operations and versions resolve deterministically;
- unhealthy or untrusted providers are excluded;
- permission and safety requirements remain explicit;
- adding unknown hardware requires a contract and provider, not core changes.
