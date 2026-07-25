# FAS-007 — Forge Decision Ledger and Evidence Architecture

Status: Production specification  
Version: 1.0.0  
Depends on: FAS-006 — Forge Event System  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

FAS-007 defines the permanent, inspectable record of why Forge made, proposed,
approved, rejected, deferred, or reversed a decision.

The Decision Ledger is not an AI transcript and is not a debug log. It is a
structured chain of decision records linked to the evidence, policies,
capabilities, actors, and Forge events that materially influenced an outcome.
It must allow a user, Forge Architect, AI Council member, or authorized auditor
to answer:

- What was decided?
- Who or what had authority to decide it?
- Which evidence was considered?
- Which policy and safety limits applied?
- How confident was Forge?
- What alternatives were rejected, and why?
- Can the decision be challenged, superseded, or rolled back?
- Did the executed action match the approved decision?

## 2. Design rules

1. **Users decide; automation assists or follows.** A readiness level never
   creates authority that the active user and policy do not grant.
2. **Append-only history.** Accepted ledger records are never silently edited or
   deleted. Corrections and reversals are new linked records.
3. **Evidence before conclusion.** A decision cannot be accepted without at
   least one evidence reference or an explicit `insufficient_evidence`
   disposition.
4. **Claims are not evidence.** Every evidence item identifies its source,
   capture time, integrity digest, and relationship to a claim.
5. **Proposals are not actions.** AI reasoning produces a proposal. An
   authorized decision and a separately recorded execution event are required
   before a mutable action is treated as complete.
6. **Unknown hardware remains representable.** Evidence and decisions reference
   capability identifiers, not hard-coded printer or accessory classes.
7. **Minimum necessary disclosure.** The ledger records decision-relevant
   facts, not unrestricted private data or hidden model reasoning.
8. **No fabricated certainty.** Confidence, uncertainty, conflicts, and missing
   inputs are first-class fields.
9. **Verifiable linkage.** Every record can link to FAS-006 event identifiers,
   configuration versions, policy versions, and prior ledger records.
10. **Fail closed for unsafe authority gaps.** Missing authority, broken
    integrity, or unresolved safety-policy conflict blocks execution.

## 3. Scope

FAS-007 applies to decisions that can materially affect:

- print start, pause, resume, cancellation, or emergency stop;
- machine motion, heating, cooling, extrusion, power, or enclosure behavior;
- calibration and persistent printer configuration;
- hardware, material, bed, nozzle, extruder, or capability selection;
- automation-readiness level behavior;
- AI detection thresholds and responses;
- preset creation, promotion, certification, or community sharing;
- user notifications that assert a safety or failure conclusion;
- security, trust, access, or integration state;
- data retention, evidence sharing, and model-training eligibility.

Routine telemetry and high-volume observations remain in their source systems.
Only evidence cited by a decision is promoted into the evidence index.

## 4. Record model

### 4.1 Decision record

A decision record is the immutable envelope for one decision state.

Required identity and timing:

- `decision_id`: globally unique, stable identifier;
- `schema_version`: schema used to validate the record;
- `recorded_at`: UTC timestamp when accepted by the ledger;
- `occurred_at`: UTC timestamp when the decision was made;
- `correlation_id`: links the decision to a print, request, workflow, or
  incident;
- `causation_event_id`: FAS-006 event that triggered evaluation.

Required decision content:

- `decision_type`: stable namespaced type;
- `summary`: concise human-readable outcome;
- `disposition`: `proposed`, `approved`, `rejected`, `deferred`, `blocked`,
  `superseded`, or `revoked`;
- `requested_action`: normalized action Forge evaluated;
- `effective_action`: action authorized after policy and safety constraints;
- `alternatives`: materially considered alternatives and rejection reasons;
- `rationale`: bounded, user-readable explanation;
- `confidence`: numeric score, calibration state, and uncertainty notes.

Required authority content:

- `proposer`: user, service, model, council, or integration that proposed it;
- `decider`: actor with authority for the disposition;
- `authority_basis`: role, readiness level, policy grant, and scope;
- `required_approvals`: approvals demanded by policy;
- `approvals`: verified approval records actually supplied.

Required traceability:

- `evidence_refs`: evidence identifiers and the claims they support or oppose;
- `policy_refs`: exact policy identifiers and versions evaluated;
- `capability_refs`: printer or subsystem capabilities involved;
- `configuration_refs`: immutable configuration or preset versions;
- `related_decision_ids`: prior, parent, dependency, conflict, or superseded
  decisions;
- `expected_event_types`: FAS-006 events expected if execution occurs.

Required integrity:

- `previous_record_hash`: prior accepted record hash for the same ledger
  partition;
- `record_hash`: canonical record digest;
- `signature`: signer, algorithm, key identifier, and signature value;
- `retention_class`: applicable retention policy.

### 4.2 Evidence record

An evidence record is an immutable description of a decision-relevant source.
It may reference bytes stored elsewhere, but the ledger must retain enough
information to detect substitution or loss.

Every evidence record includes:

- `evidence_id`, `schema_version`, and UTC capture time;
- `evidence_type` and media/content type;
- `source` identity, source class, and acquisition method;
- `subject_refs` for the print, device, capability, material, user-controlled
  configuration, or incident;
- one or more bounded `claims`;
- `supports` and `opposes` claim relationships;
- integrity digest and optional signature;
- quality assessment, known limitations, and confidence;
- privacy classification, consent basis, and retention class;
- storage reference or inline value subject to size and privacy limits.

Evidence quality is assessed independently of whether it supports the favored
outcome. A low-quality supporting item cannot be promoted merely because it
agrees with a model or administrator.

### 4.3 Amendment record

An accepted record is corrected through an amendment:

- identifies the target decision or evidence record;
- states the correction and reason;
- provides replacement fields where permitted;
- preserves the original record;
- is independently authorized, hashed, signed, and timestamped.

An amendment cannot erase an executed unsafe action or rewrite the authority
that existed at execution time.

## 5. Actors and authority

| Actor | May propose | May decide | May execute | Notes |
| --- | --- | --- | --- | --- |
| End user | Yes | Within granted user scope | Within readiness and policy limits | Always receives a readable explanation for material decisions |
| Forge Admin / ARL 5 | Yes | Within administrative policy | Within explicit admin scope | Administrative authority is logged; it does not bypass Sentinel |
| Forge Architect | Yes | Architecture and policy-design scope | No implicit machine authority | Defines system structures and policy proposals |
| AI Council | Yes | Advisory consensus only unless a policy explicitly grants bounded authority | No implicit machine authority | Council results remain attributable to individual members |
| Sentinel | Yes | May block on security or safety policy | May invoke only pre-authorized protective actions | Sentinel data access remains purpose-limited |
| Forge service | Yes | Only deterministic, policy-granted cases | Only authorized effective actions | Service identity and version are required |
| External integration | Yes | No, unless explicitly trusted by policy | No direct execution by default | Inputs are untrusted evidence until validated |

The Forge Architect and AI Council remain distinct:

- The **Forge Architect** owns architectural intent, interfaces, invariants, and
  policy design proposals.
- The **AI Council** provides plural analysis, challenges assumptions, reports
  dissent, and recommends outcomes.
- Neither role automatically receives unrestricted printer control.
- A combined workflow may use both, but the ledger records their contributions
  separately and names the actual authorized decider.

## 6. Decision lifecycle

1. FAS-006 emits a trigger event.
2. Forge opens a decision context and snapshots relevant configuration,
   capability, policy, and readiness versions.
3. Evidence collectors acquire or reference bounded evidence records.
4. Validators check provenance, integrity, freshness, applicability, consent,
   conflicts, and minimum evidence requirements.
5. One or more actors propose outcomes.
6. Policy evaluates authority, required approvals, safety constraints, and
   allowed actions.
7. The authorized decider approves, rejects, defers, or blocks the proposal.
8. The ledger canonicalizes, hashes, signs, and appends the decision.
9. An execution service consumes only an `approved` effective action.
10. FAS-006 execution and outcome events are linked back to the decision.
11. A reconciliation process verifies that observed execution matched the
    authorized action.
12. Later challenges, corrections, reversals, or superseding decisions append
    new linked records.

## 7. Evidence quality and conflict handling

Evidence quality uses explicit dimensions rather than one opaque score:

- source authenticity;
- integrity verification;
- time relevance and freshness;
- subject and capability applicability;
- measurement precision;
- completeness;
- independence from other evidence;
- known bias or contamination;
- reproducibility;
- privacy and consent validity.

Conflicting evidence is preserved and flagged. Forge must not discard dissenting
evidence solely to increase confidence. A decision containing unresolved
material conflict must:

- reduce calibrated confidence;
- name the conflict in the rationale;
- identify the policy rule allowing the disposition; and
- request user or administrator review when required by readiness or safety
  policy.

## 8. Confidence

Decision confidence is not authority and does not override policy.

The record stores:

- `score`: normalized value from 0 through 1;
- `method`: versioned calibration method;
- `calibration_state`: `uncalibrated`, `provisional`, `calibrated`, or
  `degraded`;
- `sample_context`: applicable model, printer capability, material, or
  operating context;
- `uncertainty`: bounded human-readable limitations.

Community profile confidence may describe increasing confidence after 20
qualifying prints and very high confidence after 200 successful qualifying
prints, but those labels require versioned qualification rules and do not
replace direct evidence for the current printer and print.

## 9. AI transparency boundary

Forge records:

- model or service identity and version;
- prompt/policy template identifier where applicable;
- bounded proposal and conclusion;
- cited evidence;
- confidence and uncertainty;
- dissent and alternative outcomes;
- tool or subsystem actions requested.

Forge does not require or expose unrestricted hidden chain-of-thought. The
user-facing rationale must be a concise explanation derived from decision
inputs and policy evaluation. This provides meaningful transparency without
making private internal reasoning a control surface.

## 10. Privacy and evidence sharing

Each evidence record declares:

- privacy class: `public`, `community`, `account`, `local_sensitive`, or
  `security_restricted`;
- collection purpose;
- consent basis;
- permitted uses;
- retention class;
- redaction status;
- training eligibility, which defaults to false unless policy and consent allow
  it.

Local-only evidence can still participate in a local decision. Community
sharing creates a separately authorized export record containing only the
permitted, minimized representation. User-created presets may require
community/AI sharing under the applicable Forge contribution policy, but the
decision ledger must record that policy and consent state at the time of
publication.

## 11. Storage and integrity

The logical architecture contains:

- append-only decision partitions;
- append-only evidence metadata partitions;
- content-addressed evidence objects;
- a canonicalization service;
- a hash-chain verifier;
- a signing service with rotated key identifiers;
- query projections for the dashboard and reports;
- reconciliation workers consuming FAS-006 events;
- retention and legal-hold workers.

Canonical JSON uses UTF-8, deterministic key ordering, no insignificant
whitespace, normalized number representation, and UTC timestamps. `record_hash`
is computed over the canonical record with the signature value and
`record_hash` field omitted.

Ledger partitions may be scoped by installation and time window to avoid an
unbounded single chain. Each closed partition publishes a signed root manifest
containing its first hash, final hash, record count, and previous partition root.

## 12. FAS-006 event contracts

FAS-007 consumes:

- `forge.decision.requested`;
- `forge.evidence.captured`;
- `forge.policy.changed`;
- `forge.capability.changed`;
- `forge.configuration.changed`;
- `forge.print.risk.detected`;
- `forge.security.finding.detected`.

FAS-007 emits:

- `forge.decision.proposed`;
- `forge.decision.approved`;
- `forge.decision.rejected`;
- `forge.decision.deferred`;
- `forge.decision.blocked`;
- `forge.decision.superseded`;
- `forge.decision.revoked`;
- `forge.decision.execution_requested`;
- `forge.decision.execution_reconciled`;
- `forge.ledger.integrity_failed`;
- `forge.evidence.validation_failed`.

Every emitted event includes `decision_id`, `correlation_id`, record hash, schema
version, actor reference, and event time. Execution consumers reject an action
whose referenced decision cannot be verified.

## 13. Query and dashboard requirements

Authorized users can query by:

- printer, print, file, job, incident, or correlation identifier;
- time range and decision type;
- proposer, decider, or executing service;
- disposition, confidence, policy, or readiness level;
- capability, component, material, preset, or configuration version;
- evidence source, quality, privacy class, or integrity state;
- supersession, amendment, or execution mismatch.

The default dashboard view shows the decision summary, authorized actor,
evidence count, confidence, policy result, effective action, execution result,
and any unresolved conflict. It never requires raw model reasoning to explain a
decision.

## 14. Failure behavior

| Failure | Required behavior |
| --- | --- |
| Missing required evidence | Block or defer according to policy; never invent evidence |
| Invalid evidence digest | Quarantine evidence and emit validation failure |
| Broken decision chain | Stop affected decision execution and alert Sentinel |
| Signing unavailable | Do not accept mutable-action decisions |
| Unknown schema version | Preserve record but reject execution |
| Missing authority | Block decision |
| Approval expired or mismatched | Block execution |
| Event bus unavailable | Persist to durable outbox; do not claim publication |
| Ledger unavailable | Fail closed for material mutable actions |
| Execution differs from decision | Emit reconciliation failure and escalate by policy |
| Privacy policy conflict | Minimize or withhold evidence; never broaden access implicitly |

Emergency protective actions pre-authorized by safety policy may execute during
a ledger outage only when the action, conditions, and maximum scope were
previously signed. The action must be backfilled and reconciled when service
returns.

## 15. Minimum APIs

- `submitEvidence(evidence)`
- `validateEvidence(evidenceId)`
- `requestDecision(context)`
- `submitProposal(decisionId, proposal)`
- `recordDecision(decision)`
- `authorizeExecution(decisionId)`
- `recordExecutionOutcome(decisionId, eventId)`
- `amendRecord(amendment)`
- `supersedeDecision(previousDecisionId, decision)`
- `verifyRecord(recordId)`
- `verifyPartition(partitionId)`
- `queryDecisionHistory(filters)`
- `exportDecisionExplanation(decisionId, audience)`

APIs must be idempotent, authenticated, authorized, schema-validated, and
correlation-aware. Repeated commands with the same idempotency key return the
original accepted result.

## 16. Acceptance criteria

FAS-007 is production-ready when:

1. Invalid records fail schema validation.
2. Canonicalization and hashing are deterministic across supported runtimes.
3. Tampering with any chained record is detected.
4. AI proposals cannot directly execute printer actions.
5. Missing authority or required approval blocks execution.
6. An approved decision can be traced to its evidence, policy, configuration,
   capabilities, trigger event, execution event, and outcome.
7. Amendments and superseding decisions preserve the original history.
8. Conflicting and dissenting evidence remains inspectable.
9. Privacy and consent constraints apply to queries and exports.
10. Unknown hardware is representable through capability references without
    schema redesign.
11. Ledger and event outbox recovery is tested.
12. Execution reconciliation detects unauthorized or divergent behavior.
13. User-facing explanations omit hidden reasoning while remaining sufficient
    to understand the outcome.
14. Retention, partition closing, key rotation, and verification are tested.

## 17. Explicit non-goals

FAS-007 does not:

- store all raw telemetry;
- replace FAS-006 event delivery;
- grant AI systems authority merely because they agree;
- make confidence a safety policy;
- expose unrestricted hidden model reasoning;
- hard-code supported printer brands or component catalogs;
- allow administrators to rewrite accepted history;
- treat a successful API call as proof that a physical action occurred.

## 18. Next production dependency

FAS-008 should define the Forge Policy Decision and Authorization Engine that
evaluates actor authority, automation readiness, approvals, safety constraints,
and effective actions before a FAS-007 decision can be accepted for execution.
