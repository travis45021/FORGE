# FAS-037 - FORGE v1.0 Baseline Release Scope

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-036

FAS-037 defines the final release evidence gate. Constitution, licensing,
tests, documentation, four-click workflow, hardware integration, recovery,
packaging, and security must all be explicitly evidenced. Future-gated AI,
distributed, shared-evidence, and autonomy features remain excluded.

The gate reports whether a release is blocked or ready for a final human
decision. It never self-approves, publishes, starts hardware, or changes the
approved release scope.

The reference evaluator accepts exactly the nine named evidence gates as
explicit booleans, rejects unknown gates and malformed review identity or UTC
timestamps, and returns the reviewed evidence with a deterministic SHA-256
digest. Its strict schema keeps both release and physical-execution authority
false even when all evidence is ready for a final human decision.

The evaluator also rejects obvious automation, CI, bot, and system reviewer
labels. This is a fail-closed guard against self-approval, not proof that an
identity is human; the final release decision still requires an accountable
human reviewer and the complete external evidence package.
