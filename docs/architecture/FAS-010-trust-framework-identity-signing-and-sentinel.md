# FAS-010 — Trust Framework, Identity, Signing, and Sentinel

Status: Production specification  
Version: 1.0.0  
Depends on: FAS-001, FAS-002, FAS-003, FAS-005, FAS-006, FAS-007, FAS-008, FAS-009  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

FAS-010 defines the trust evidence required by authorization and policy-bundle
governance. It verifies identity, key state, signatures, approvals,
attestations, rotation, and revocation without turning official origin, brand,
or Sentinel inference into authority.

Trust answers whether a claim is sufficiently verified for a declared purpose.
FAS-008 separately decides whether an authenticated actor is authorized.
FAS-009 separately governs immutable policy-bundle lifecycle.

## 2. Invariants

1. Trust is verified, not inferred from names, brands, popularity, network
   location, repository ownership, or an `official` label.
2. Compatibility and trust are separate. Custom hardware and modified FORGE
   builds may establish trust under their own identities.
3. Every signature binds canonical payload bytes, an exact key, an algorithm,
   and a declared purpose.
4. A key is usable only inside its validity interval and allowed purposes.
5. Revocation blocks verification at or after its effective time. It never
   rewrites earlier ledger evidence.
6. Rotation introduces a new key identity and preserves predecessor/successor
   lineage. It never mutates old signed records.
7. A valid signature proves control of a key and payload integrity. It does not
   prove compatibility, safety, quality, constitutional compliance, or
   authorization.
8. Approvals bind an exact subject digest, approval type, approver identity,
   time window, and signature.
9. Sentinel produces evidence and recommendations. It cannot grant authority,
   broaden permissions, silently delete software, or directly control hardware.
10. Deterministic narrow emergency controls may block or isolate within their
    declared authority and must immediately record what occurred.
11. Local verification remains possible without network access when required
    keys, revocation state, and policy snapshots are locally available.
12. Failure is closed for the requested trust claim and explained with stable
    reason codes.

## 3. Identity and key model

Trust identities may represent projects, releases, builds, installations,
nodes, users, organizations, services, plugins, capability providers, devices,
or AI models. Display labels, hostnames, SSIDs, IP addresses, and repository
names are not sufficient identity.

A verification key declares:

- immutable `key_id`;
- owning `subject_id`;
- algorithm;
- verification material or a protected verifier reference;
- allowed signature purposes;
- validity interval;
- predecessor key, if rotated;
- lifecycle status and optional revocation record.

Production adapters should use asymmetric algorithms and hardware-backed or
isolated signing where appropriate. Private signing material is never stored in
the public verification registry.

## 4. Signature purposes

Purposes prevent one valid key from silently authorizing every kind of claim.
Initial purposes include:

- `forge.signature.release`
- `forge.signature.policy_bundle`
- `forge.signature.approval`
- `forge.signature.attestation`
- `forge.signature.node`
- `forge.signature.plugin`

New purposes require a documented contract. A verifier rejects a signature when
the key does not explicitly allow its purpose.

## 5. Canonical payload binding

The reference component accepts JSON-compatible values and serializes them with
UTF-8, sorted object keys, no insignificant whitespace, and no non-finite
numbers. The resulting SHA-256 digest is recorded in every verification result.

Production protocols may use another canonicalization only when the exact
canonicalization identifier is versioned and included in the signed contract.

## 6. Verification result

Successful verification returns a structured attestation containing:

- attestation identifier;
- schema version;
- subject and key identity;
- algorithm and purpose;
- canonical payload digest;
- verifier identity and version;
- evaluation time;
- `verified` outcome;
- stable reason codes;
- key lineage and revocation state references.

Rejected claims raise a typed trust error in the reference component.
Production services must also publish FAS-006 events and persist appropriate
FAS-007 evidence for both acceptance and rejection.

## 7. Rotation and revocation

Key rotation requires:

- a new immutable key identifier;
- the same subject unless an explicit identity migration is governed;
- a predecessor reference;
- a non-overlapping or deliberately bounded activation plan;
- proof authorized by the predecessor or a separately governed recovery path.

Revocation records contain the key, effective time, reason, and verified
governance authority. Revocation does not delete the key because historical
records must remain reconstructable.

Compromise may require rejecting claims whose evaluation time predates the
revocation announcement according to policy. That retrospective incident policy
belongs to governance and must not be invented by the verifier.

## 8. Approval verification

An approval is valid only when:

- its approval identifier and type are present;
- it names an approver identity;
- it binds the exact subject digest under evaluation;
- evaluation occurs at or after approval time and before expiry;
- its signature uses `forge.signature.approval`;
- the key belongs to the named approver;
- the key is valid and not revoked at evaluation time.

FAS-008 and FAS-009 determine how many approvals and which approval types are
required. FAS-010 verifies supplied approval claims; it does not choose policy.

## 9. Sentinel boundary

Sentinel evidence includes model identity/version, evidence references,
confidence, limitations, recommendation, affected scope, and evaluation time.
Recommendations are:

- `allow_evidence` — no trust concern found; never an authorization grant;
- `challenge` — more verification or user/administrator review is required;
- `block` — policy should deny the evaluated action;
- `quarantine` — isolate the component through a separately authorized
  deterministic control.

Sentinel is inspectable and replaceable. Its inference alone never receives
unrestricted immediate-enforcement authority. If Sentinel is unavailable,
deterministic security and ordinary local control continue; operations that
explicitly require Sentinel evidence fail closed or require a policy-approved
alternative.

## 10. Modified and community builds

FORGE distinguishes:

- official signed build;
- community signed build;
- locally modified build;
- unsigned development build;
- corrupted or unexpectedly modified build;
- revoked or known-compromised build.

A local modification is not automatically malware. It changes the evidence and
trust state and must be explained accurately. Shared services may impose
stronger identity and integrity requirements without preventing local use.

## 11. Events

FAS-010 defines these event families:

- `forge.trust.key.registered`
- `forge.trust.key.rotated`
- `forge.trust.key.revoked`
- `forge.trust.signature.verified`
- `forge.trust.signature.rejected`
- `forge.trust.approval.verified`
- `forge.trust.approval.rejected`
- `forge.sentinel.evidence.recorded`
- `forge.sentinel.block.recommended`
- `forge.sentinel.quarantine.recommended`

Sensitive key material and signatures should be referenced or access-controlled,
not copied into broadly visible event payloads.

## 12. Reference implementation boundary

`src/forge/fas/trust.py` provides:

- immutable in-memory key registration;
- canonical payload digests;
- injectable algorithm verifiers;
- purpose, subject, validity, rotation, and revocation enforcement;
- signed approval verification;
- structured trust attestations;
- constrained Sentinel evidence validation;
- deterministic governance history.

The included HMAC helper is explicitly for examples and tests. It is not a
production release-signing design.

Production adapters must add durable transactional storage, approved asymmetric
cryptography, protected key services, identity authentication, governed
recovery/rotation, trusted time, revocation distribution, malware-scanner
integration, FAS-006 publication, FAS-007 persistence, rate limits, and
concurrent consistency controls.

## 13. Acceptance criteria

FAS-010 is production-ready when:

1. its schemas compile under JSON Schema Draft 2020-12;
2. examples validate;
3. tampered payloads fail verification;
4. wrong subjects, purposes, algorithms, and keys fail closed;
5. expired, not-yet-valid, and revoked keys fail closed;
6. rotation preserves immutable lineage;
7. approvals bind exact digests and validity windows;
8. Sentinel evidence cannot be mistaken for authorization;
9. unknown hardware identities are not restricted by manufacturer lists;
10. the complete FAS suite passes.

## 14. Next production dependency

FAS-012 should define user interaction, suggestions, attention budgets,
AI-free operation, and the `You decide. Forge follows.` contract. FAS-011 AI
Council remains future-gated and is not required to continue the local v1
baseline.

