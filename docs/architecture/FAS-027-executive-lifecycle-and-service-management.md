# FAS-027 - Executive Lifecycle and Service Management

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-026

FAS-027 defines the local service lifecycle boundary for FORGE. Services are
registered with explicit dependencies and provided capabilities, then moved
through observable states only with a user-scoped authority reference.
Manifest dependencies and provided capabilities are unique, non-empty names,
and a service cannot depend on itself.

The reference implementation in `src/forge/fas/lifecycle.py` provides service
registration, constrained state transitions, explicit start/stop plans, and a
local history. Lifecycle observations are accepted only as parseable UTC
timestamps ending in `Z`, so state history cannot silently mix local times.
Plans do not spawn processes, issue printer commands, resume
runtime contexts, or grant authority. A production supervisor may add process
control, dependency resolution, health probes, crash recovery, and durable
state while preserving those boundaries.

`src/forge/fas/process_supervision.py` now provides a contract-only,
shell-free local process evidence adapter. It records completion, crash, and
timeout outcomes with output digests and explicitly grants no physical or
release authority. It does not enforce OS memory/disk quotas and is not a
production Orca launcher; those reviewed platform controls remain open.

Automatic restart is not an authority source. Any recovery that could affect a
physical device must remain paused until FAS-007 authorization, FAS-010 trust,
FAS-023 health, FAS-022 runtime, and the user's final print confirmation are
freshly satisfied.
