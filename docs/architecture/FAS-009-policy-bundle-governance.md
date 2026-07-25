# FAS-009 — Policy Bundle Governance

Status: Production specification  
Version: 1.0.0  
Depends on: FAS-001, FAS-006, FAS-007, FAS-008  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

FAS-009 governs how authorization policies become an immutable, reviewable,
signed policy bundle and how that bundle moves into or out of service. It
prevents mutable individual files, model proposals, administrative convenience,
or deployment races from silently changing FORGE authority.

## 2. Invariants

1. The FORGE Constitution is the highest authority; a bundle that cannot prove
   constitutional compatibility cannot activate.
2. Sentinel may block activation or rollback but may never broaden authority.
3. Only an authenticated Forge Admin may perform activation or rollback.
   Forge Architect and AI Council can provide required approvals, proposals,
   challenges, and dissent, but neither has implicit execution authority.
4. Bundle content is canonical, content-addressed, signed, and immutable after
   registration.
5. Policy references identify exact versions and digests. Floating versions,
   network discovery, and ambient configuration are forbidden at evaluation.
6. Activation is atomic per channel. A channel resolves to one complete bundle,
   never a mixture of old and new policies.
7. Rollback is a new, recorded governance action to a registered ancestor; it
   never erases history or mutates the failed bundle.
8. Every registration, rejection, activation, no-op, and rollback produces
   FAS-007 evidence and a FAS-006 event.
9. Policy matching remains capability-based. Bundles must not impose a closed
   list of printer brands, hotends, accessories, or user-defined hardware.
10. Failure is closed: invalid schema, digest, signature, lineage, approval,
    constitutional state, Sentinel state, or storage integrity blocks change.

## 3. Bundle lifecycle

Bundles are authored outside the active registry, validated as `candidate`,
registered immutably, and then activated on a named channel. Operational states
are registry facts rather than mutable fields inside signed bundle content.

Channels are `development`, `canary`, and `production`. Bundle rollout bounds
constrain the percentage an activation may select. Production rollout may be
incremental, but each affected evaluator receives one whole bundle.

## 4. Required gates

Activation and rollback require:

- a registered bundle whose content digest recomputes exactly;
- at least one trust-service-verified bundle signature;
- verified Constitution and Sentinel attestations embedded in the bundle;
- a live clear Sentinel state at transition time;
- an authenticated `admin` actor in the `forge_admin` role;
- the bundle’s named, unique, unexpired verified approvals;
- an allowed channel and rollout percentage;
- an intact Decision Ledger and policy registry.

Approval types are policy data. A production bundle may require independent
Forge Architect, AI Council, security, or user-governance approval, while the
Forge Admin remains the only activating actor. Approval does not itself execute.

## 5. Versioning and lineage

`bundle_id` is globally unique and immutable. `version` uses semantic versioning
for human governance; `content_digest` is the machine identity. Every successor
identifies one registered parent. The initial bundle has a null parent.

Rollback targets must be registered ancestors of the active bundle. Arbitrary
sideways activation is a normal new activation and must pass its own review.
Revocation blocks future activation but does not rewrite prior ledger records.

## 6. Events and ledger evidence

FAS-009 emits:

- `forge.policy_bundle.registered`
- `forge.policy_bundle.rejected`
- `forge.policy_bundle.activated`
- `forge.policy_bundle.activation_noop`
- `forge.policy_bundle.rolled_back`
- `forge.policy_bundle.revoked`

Records contain the governance identifier, bundle identifier and digest,
channel, previous bundle, rollout percentage, actor, time, approval references,
constitutional and Sentinel attestations, and outcome. Sensitive signature
material is referenced rather than copied into broadly visible events.

## 7. Reference implementation boundary

`PolicyBundleRegistry` demonstrates deterministic digest verification,
immutability, activation gates, atomic channel state, ancestor-only rollback,
idempotent activation, and governance history. Production adapters must provide
durable transactional storage, cryptographic verification, identity and
approval verification, revocation checking, FAS-006 publication, and FAS-007
ledger persistence.
