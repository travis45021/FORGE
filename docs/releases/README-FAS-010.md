# FORGE FAS-010

FAS-010 defines trust verification, identity, signing, key rotation and
revocation, signed approvals, and the Sentinel evidence boundary. See
`docs/architecture/FAS-010-trust-framework-identity-signing-and-sentinel.md`.

Included:

- strict Draft 2020-12 key and trust-attestation schemas;
- a non-production deterministic signing example;
- an injectable reference trust service;
- immutable key lineage and governed revocation;
- exact payload and approval binding;
- constrained, explicitly non-authoritative Sentinel evidence;
- behavioral and schema regression tests.

The included HMAC algorithm is for tests and examples only. Production adapters
must use approved asymmetric verification and protected signing infrastructure.
