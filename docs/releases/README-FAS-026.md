# FAS-026 Reference Implementation

FAS-026 implements the local data ownership, persistence, backup, and recovery
reference contract through forge.fas.persistence.DataRecoveryService.

It provides data classes, provenance-backed integrity records, digest-verified
backup manifests, secret separation, portable export, explicit restore modes,
conflict reporting, replay-safe recovery results, and backup-gated migration
planning.

The service is intentionally in-memory. Filesystem durability, encryption
providers, crash-atomic transactions, and application lifecycle integration
remain on the dependency-correct path toward v1.0.
