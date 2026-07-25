# FAS-008 — Forge Policy Decision and Authorization Engine

Status: Production specification  
Version: 1.0.0  
Depends on: FAS-006 — Forge Event System; FAS-007 — Forge Decision Ledger  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

FAS-008 defines the deterministic control point that decides whether a proposed
Forge action is allowed, denied, or requires an explicit approval challenge.
It turns versioned policy, verified identity, delegated authority, automation
readiness, approvals, Sentinel state, and current facts into a bounded
`effective_action`.

The engine authorizes; it does not execute. Only a separately authenticated
executor may consume an allowed result, and only after the corresponding
FAS-007 decision is approved, current, signed, and integrity-verified.

## 2. Non-negotiable invariants

1. **Users decide; automation assists or follows.** Readiness never creates
   authority that identity, role, scope, policy, and approvals do not grant.
2. **Default deny.** Unknown actions, missing allow rules, invalid input,
   unavailable policy, or ambiguous authority cannot execute.
3. **Deny overrides.** An applicable deny rule wins over every allow rule,
   regardless of rule order or priority.
4. **Sentinel can block but cannot silently broaden access.** A Sentinel block,
   policy-integrity failure, or ledger-integrity failure is terminal.
5. **Proposals cannot execute.** AI models, the AI Council, integrations, and
   the Forge Architect have no implicit machine authority.
6. **Confidence is not authority.** Risk or confidence scores may become policy
   facts but cannot independently grant an action.
7. **Effective actions are bounded and visible.** Policy may reject or narrow
   parameters; it may not silently make an action more permissive.
8. **Evaluation is reproducible.** The same normalized request and policy set
   produce the same evaluation identity, outcome, and effective action.
9. **No ambient authority.** Policies, identity facts, scopes, approvals, time,
   and decision state are explicit inputs.
10. **Capability-based extensibility.** Unknown printers, accessories, and user
    hardware remain valid targets. New capability identifiers do not require
    engine redesign.

## 3. Automation Readiness Level enforcement

FAS-008 treats readiness as one input to authority, never as authority itself.
The v1.0 exposure rules are:

| ARL | v1.0 availability | Authorization behavior |
| --- | --- | --- |
| 0 | End user | Advisory only; mutable execution requires a separately granted action path |
| 1 | End user | User-directed actions require policy, scope, and action-specific approval |
| 2 | Restricted | Feature-gated; unavailable without explicit restricted access |
| 3 | Restricted | Feature-gated; unavailable without explicit restricted access |
| 4 | Restricted | Feature-gated; unavailable without explicit restricted access |
| 5 | Forge Admin only | Requires an authenticated admin actor and explicit administrative policy |

ARL 2–4 remain inaccessible to ordinary end users in v1.0. ARL 5 remains
inaccessible to end users. Forge Admin authority still cannot bypass Sentinel,
policy integrity, ledger integrity, or a non-delegable safety denial.

## 4. Inputs

An authorization request contains:

- stable request and idempotency identifiers;
- evaluation time supplied by a trusted caller;
- `decision` or `execution` phase;
- verified actor identity, actor type, version, and active role;
- active automation readiness level;
- granted scopes;
- normalized requested action, target references, and parameters;
- verified, expiring approvals;
- bounded facts from preflight, capabilities, configuration, privacy, security,
  and safety systems;
- current FAS-007 decision state.

The engine receives a complete immutable policy set for the evaluation. It does
not discover policy from environment variables, network services, mutable
global state, or action target brands.

## 5. Policy model

Every policy is independently versioned and includes:

- stable policy identifier and version;
- enable state and priority;
- `allow` or `deny` effect;
- one or more namespaced action patterns;
- granted actor types and roles;
- minimum and maximum readiness level;
- required scopes;
- required approval types and counts;
- exact-match applicability facts;
- parameter constraints;
- post-authorization obligations.

Priority chooses among compatible allow policies. Priority never defeats an
applicable deny.

Action patterns apply to the namespaced action type, not to printer brands or a
closed hardware enumeration. Exact matches are preferred for material actions.
Wildcards are permitted only where policy review establishes a bounded family.

## 6. Combining algorithm

For each request, the engine:

1. validates and canonicalizes the request and every policy;
2. verifies hard invariants including Sentinel, ledger, readiness, and execution
   decision state;
3. calculates the digest of the sorted policy set;
4. selects enabled policies whose action pattern and applicability facts match;
5. returns `deny` if any applicable deny policy exists;
6. returns `deny` if no applicable allow policy exists;
7. evaluates compatible allow policies in descending priority;
8. verifies actor type, role, readiness bounds, and required scopes;
9. verifies unique, unexpired, cryptographically verified approvals;
10. applies parameter constraints using explicit `reject` or `clamp` behavior;
11. returns `allow`, `deny`, or `challenge`;
12. emits a complete result for FAS-007 recording and FAS-006 publication.

The `challenge` outcome means policy could allow the action after named approval
requirements are satisfied. It is not permission to execute.

## 7. Approval rules

Approvals are:

- bound to a unique approval identifier;
- typed and counted by policy;
- accepted only within their validity interval;
- ignored when signature or identity verification fails;
- deduplicated by approval identifier;
- bound by the approval service to the request, action digest, actor, and
  correlation context before reaching the evaluator.

The reference evaluator consumes a `verified` fact because cryptographic
verification belongs to the trust service. A production adapter must fail
closed if verification status cannot be proven.

An approval used at ARL 1 is action-specific. “Don’t ask again” user preferences
may select a standing policy only when that policy is explicit, revocable,
time-bounded where appropriate, and visible to the user.

## 8. Parameter constraints

Policies may constrain numeric action parameters:

- `reject` denies the request when a value is outside the policy range;
- `clamp` produces a narrower effective value and records the requested and
  effective values.

Constraints never invent missing required parameters, convert non-numeric
values, or increase a maximum. All applied constraints are present in the
authorization result and later FAS-007 decision explanation.

## 9. Execution authorization

An execution-phase request additionally requires:

- FAS-007 disposition `approved`;
- verified FAS-007 decision signature;
- decision not revoked or superseded;
- verified ledger integrity;
- action digest matching the approved effective action;
- policy-set digest still valid or a policy-defined re-evaluation;
- current approvals and scopes;
- clear Sentinel state.

The reference evaluator implements the decision-state, ledger, approval,
scope, readiness, policy, and Sentinel checks. Production integration must add
the cryptographic action-digest comparison at the trust boundary.

## 10. Actors and separation of duties

| Actor | Policy participation | Implicit execution authority |
| --- | --- | --- |
| End user | Requests and approves within user scope | None beyond explicit grant |
| Forge Admin | Admin policies and ARL 5 within authenticated scope | None beyond explicit grant |
| Forge Architect | Designs architecture and proposes policy | None |
| AI Council | Advises, challenges, and records dissent | None |
| AI model | Proposes bounded actions and evidence | None |
| Sentinel | Blocks and requests pre-authorized protective actions | No broad grant |
| Forge service | Evaluates or executes its assigned service scope | None outside service grant |
| Integration | Supplies untrusted requests or evidence | None by default |

Forge Architect and AI Council remain distinct. A policy can require either or
both as approval sources, but neither becomes a hidden administrator.

## 11. Decision and event integration

FAS-008 consumes:

- `forge.decision.requested`;
- `forge.decision.approved`;
- `forge.policy.changed`;
- `forge.identity.changed`;
- `forge.scope.changed`;
- `forge.approval.recorded`;
- `forge.capability.changed`;
- `forge.configuration.changed`;
- `forge.security.finding.detected`;
- `forge.ledger.integrity_failed`.

FAS-008 emits:

- `forge.authorization.allowed`;
- `forge.authorization.denied`;
- `forge.authorization.challenge_required`;
- `forge.authorization.policy_invalid`;
- `forge.authorization.revalidation_required`.

Every event carries the evaluation identifier, request identifier, policy-set
digest, outcome, reason codes, correlation identifier, and schema version. An
allow event contains the effective action digest, not unrestricted private
context.

FAS-007 records the policy references, authorization outcome, applied
constraints, approval evidence, decider, and expected execution events.

## 12. Idempotency and time-of-check

The same request identifier and idempotency key must return the originally
accepted result. Reuse of an idempotency key with different normalized input is
an integrity error.

Authorization has a bounded lifetime. Before execution, adapters revalidate
volatile facts including Sentinel state, decision currentness, approval expiry,
identity, scope, configuration, and capability version. A changed material fact
requires a new decision or a policy-defined re-evaluation; it cannot reuse a
stale allow.

## 13. Failure behavior

| Condition | Outcome |
| --- | --- |
| No matching allow | Deny |
| Matching deny and allow | Deny |
| Missing or expired required approval | Challenge |
| Invalid approval verification | Ignore approval, then challenge or deny |
| Missing role, scope, or readiness grant | Deny |
| ARL 2–4 without restricted-access gate | Deny |
| ARL 5 actor is not Forge Admin | Deny |
| Sentinel block | Deny |
| Ledger integrity not verified | Deny |
| Execution decision not approved/current/signed | Deny |
| Constraint with `reject` violated | Deny |
| Constraint with `clamp` violated | Allow only the recorded narrower action |
| Unknown action or target capability | Deny unless explicit capability-based policy allows it |
| Policy parse, schema, signature, or dependency failure | Deny and emit policy-invalid event |
| Authorization store unavailable | Fail closed for mutable actions |

Emergency protective actions require a previously signed, narrowly scoped
policy that defines triggering facts, permitted target, maximum action, expiry,
and mandatory backfill. “Emergency” is not a general bypass.

## 14. Security and privacy

- Policy bundles are signed, versioned, and content-addressed.
- Identity, approval, and scope assertions are verified before evaluation.
- Policy authors cannot grant themselves execution authority through the same
  unreviewed change.
- Sentinel security-restricted facts are reduced to decision-relevant claims.
- Authorization logs exclude credentials, raw private evidence, hidden model
  reasoning, and direct personal identifiers.
- Explanations disclose the matched rule and missing requirement without
  exposing sensitive policy internals to unauthorized actors.

## 15. Minimum APIs

- `evaluateAuthorization(request, policySet)`
- `challengeAuthorization(evaluationId)`
- `submitApproval(evaluationId, approval)`
- `revalidateAuthorization(evaluationId, currentFacts)`
- `explainAuthorization(evaluationId, audience)`
- `verifyPolicySet(policySetDigest)`
- `activatePolicyBundle(bundleId, version)`
- `revokePolicyBundle(bundleId, version)`
- `queryAuthorizationHistory(filters)`

All APIs are authenticated, schema-validated, idempotent, correlation-aware,
and produce FAS-006 events plus FAS-007 traceability.

## 16. Acceptance criteria

FAS-008 is production-ready when:

1. unknown actions and missing policies fail closed;
2. applicable deny policies always override allows;
3. actor type, role, readiness, scope, and approvals are all enforced;
4. ARL 2–4 restrictions and ARL 5 admin-only access are tested;
5. AI, Architect, Council, and integrations cannot gain implicit execution;
6. Sentinel and ledger-integrity blocks cannot be overridden;
7. execution requires an approved, signed, current FAS-007 decision;
8. expired, duplicate, mismatched, and unverified approvals cannot satisfy policy;
9. parameter rejection and visible narrowing are deterministic;
10. the same input and policy set produce the same evaluation identity;
11. unknown hardware identifiers work without source changes when capability
    policy grants the action;
12. input objects are not mutated;
13. policy bundle signature, activation, rollback, and conflict tests pass;
14. time-of-check/time-of-use revalidation is tested;
15. results validate against the published schema and can be recorded by
    FAS-007.

## 17. Explicit non-goals

FAS-008 does not:

- execute printer actions;
- replace authentication, signature verification, or the Sentinel model;
- make model confidence an authority grant;
- infer permission from a role name alone;
- expose chain-of-thought;
- hard-code supported printer or accessory catalogs;
- allow policy priority to override a deny;
- treat a challenge as an allow;
- permit an administrator to bypass non-delegable safety invariants.

## 18. Reference implementation boundary

`src/forge/fas/authorization.py` is a deterministic, standard-library reference
evaluator and executable statement of the core combining rules. Production
services must add durable idempotency storage, schema validation at ingress,
cryptographic policy and approval verification, policy bundle lifecycle,
event/outbox integration, FAS-007 persistence, rate limits, and concurrent
revalidation.

## 19. Next production dependency

FAS-009 should define policy bundle governance, signing, activation, staged
rollout, rollback, conflict analysis, and change approval so FAS-008 never
evaluates an untrusted or ambiguously active policy set.

