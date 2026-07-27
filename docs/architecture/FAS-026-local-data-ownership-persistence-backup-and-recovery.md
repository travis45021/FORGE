# FAS-026 - Local Data Ownership, Persistence, Backup, and Recovery

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-025
Depends on: FAS-006, FAS-007, FAS-009, FAS-012, FAS-013, FAS-018, FAS-019, FAS-020, FAS-021, FAS-022, FAS-023, FAS-024, FAS-025

## Principle

User Forge knowledge, configurations, evidence, and history belong to the user
and remain usable locally without a cloud account. Persistence preserves
records and recovery evidence; it never grants authority or replays physical
work.

## Scope

FAS-026 defines:

- local data classes and authoritative sources;
- JSON-compatible durable records with provenance and SHA-256 integrity;
- manual local backup manifests and deterministic payload digests;
- explicit secret separation and encrypted, confirmed secret backups;
- inspect-only, selected-record, configuration/profile, full-workspace, and
  runtime-recovery review restore modes;
- conflict-preserving restore behavior;
- migration plans that require a verified backup and user approval; and
- audit events for storage, backup, integrity, verification, and restore.

The reference implementation is in
src/forge/fas/persistence.py. The reference service remains in-memory for
record operations, and `AtomicSnapshotStore` provides crash-atomic,
integrity-checked JSON snapshots for non-secret local exports. It is not an
encryption provider or a complete filesystem database.

## Authority boundaries

- Local data is user-owned by default.
- Caches and ephemeral values are never authoritative.
- Decision Records, approved policy state, and user-verified objects remain
  authoritative for their declared purpose.
- Secrets are not ordinary records, are excluded from ordinary exports, and
  cannot be authoritative data.
- A backup, export, restore plan, or migration plan cannot authorize a Mission,
  dispatch a provider, upload an artifact, resume a printer, or start a print.
- Restore always requires user review and live re-verification before any
  physical continuation can be considered.
- Conflicting restored records are reported and preserved; good current data is
  never silently overwritten.

## Data classes

| Class | Examples | Default handling |
| --- | --- | --- |
| ephemeral | UI samples, caches, temporary queues | discardable |
| operational_state | contexts, leases, pending work | recoverable for review |
| durable_local | profiles, objects, configurations | user-retained |
| audit | Decisions, approvals, interventions | visible retention policy |
| evidence | measurements, logs, test artifacts | relevance/privacy policy |
| secret | credentials, keys, tokens | separate, excluded by default |

## Backup contract

A backup records its owner scope, selected classes, destination, encryption
state, secret inclusion, retention class, included IDs, restore modes, and
content digest. Creation does not imply that the destination is trusted:
verification recomputes the digest before restore.

Secret inclusion requires both explicit confirmation and encryption. Ordinary
backup and export paths exclude secrets.

## Restore and migration contract

The inspect_only mode produces no changes. Other modes add absent records and
report conflicts rather than overwriting changed current records. Every restore
result sets:

    hardware_resume_allowed = false
    physical_commands_replayed = false
    requires_live_reverification = true
    requires_user_review = true

Migration planning requires a known backup and produces a reversible,
user-approval-gated plan. Applying a migration is a later filesystem/service
operation and must be backed up and tested before release.

## Events

The reference service records:

    data.record.stored
    backup.created
    backup.verified
    data.integrity.failed
    restore.completed
    snapshot.loaded

Production persistence must connect these operations to FAS-006 events and
FAS-007 Decision Records without putting secret contents into the audit stream.

## First-release boundary

FAS-026 v1 scope includes local persistence for core records, manual local
backup/restore, crash-atomic non-secret snapshots, backup-before-material-change
contracts, integrity checks, portable export/import contracts, migration
planning, and separate secret handling. Cloud backup, automatic
synchronization, distributed databases, and organization retention policy
remain future work.

## Acceptance criteria

- [x] Local ownership and offline contract recorded.
- [x] Data classes and authority sources defined.
- [x] Provenance-backed records and integrity digests implemented.
- [x] Backup manifests and verification implemented.
- [x] Secret exclusion and confirmed encrypted inclusion enforced.
- [x] Restore modes and conflict reporting implemented.
- [x] Physical replay and blind resume prohibited by contract.
- [x] Migration planning requires a backup and user approval.
- [x] Schemas, examples, and behavior tests added.
- [x] Crash-atomic, non-secret filesystem snapshot contract added.

Encryption adapters, a complete filesystem database, transaction orchestration,
and migration execution remain application-integration work. Snapshot writes
use a same-directory temporary file, flush and file synchronization, then an
atomic replace; they never persist secrets.

## Decisions needed

None. The local-first ownership and restore-safety decisions were already
approved and are now implemented as a reference contract.
