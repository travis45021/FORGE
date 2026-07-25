# FAS-006 — Forge Event System

Status: Reconstructed production specification  
Version: 1.0.0  
Depends on: FAS-001 through FAS-005  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

FAS-006 is FORGE's asynchronous communication backbone. It separates events
(facts), requests (desired outcomes), commands (authorized instructions),
decisions, evidence, and state snapshots. Publishing a request is never proof
that an action was authorized or completed.

## 2. Event envelope

Every message contains `event_id`, `event_type`, `event_version`,
`occurred_at`, `published_at`, `source`, `subject`, `correlation_id`,
`causation_id`, `classification`, `payload`, `metadata`, and `trace_id`.
Namespaced event types and subjects keep unknown hardware representable.

## 3. Delivery semantics

Delivery is at least once. Consumers are idempotent by `event_id`; ordering is
guaranteed only within an explicitly named partition and monotonic sequence.
Consumers checkpoint after successful handling. Retries preserve identity and
causation. Poison messages enter a dead-letter stream with evidence, never
silent deletion.

## 4. Replay and evolution

Replay preserves the original envelope and marks replay metadata. Replayed
requests and commands cannot renew approvals or authority. Consumers declare
supported versions. Additive compatible fields retain a major version;
breaking changes publish a new major event contract and migration path.

## 5. Security and privacy

Publish and subscribe permissions are scoped by type and classification.
Security-restricted payloads are encrypted and purpose-limited. Integrity,
source authentication, schema validation, size limits, and retention are
checked before routing. Metadata must not carry secrets or hidden reasoning.

## 6. FAS integration

FAS-004 mission transitions publish state events. FAS-005 consumes requests and
publishes proposals and execution requests. FAS-007 links decisions and
evidence to event identifiers. FAS-008 publishes authorization outcomes.
Execution services accept commands only when their signed decision and
authorization references are current and verified.

## 7. Acceptance criteria

- envelopes validate deterministically;
- duplicate delivery is detectable;
- correlation, causation, trace, partition, and sequence remain intact;
- replay never creates fresh authority;
- unknown capability subjects require no event-system code change;
- event, request, command, decision, evidence, and state classifications remain
  distinct.
