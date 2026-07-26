# FAS-022 - Runtime, Execution Context, and Resources

Status: Production specification  
Version: 1.0.0  
Historical source: FAS-021  
Depends on: FAS-002 through FAS-010, FAS-014, FAS-015, FAS-018, FAS-021

## Principle and authority boundary

FORGE executes work inside a known context with known authority, known
resources, immutable snapshots, and a recoverable record. The Runtime carries
out Executive-authorized work through resolved capability providers; it cannot
invent policy, authority, hardware behavior, or successful physical outcomes.

## Execution Context

Every meaningful Mission action records:

- context, Mission, parent, and correlation identity;
- verified authority and policy snapshot;
- automation level and explicit target objects;
- allowed and resolved capabilities/providers;
- reserved resources and scoped data access;
- configuration and Verification Packet snapshots;
- time and cost limits;
- state, start time, and reason.

Child contexts may narrow inherited authority, capabilities, targets, data,
resources, time, or cost. They may never silently broaden them.

## Resources, locks, and leases

Resources declare exclusive, shared-read, or shared-limited use. The Runtime
rejects incompatible concurrent leases. Leases are time-bounded and require
verified authority to renew. Expiry places the affected context into recovery;
it does not imply that physical hardware is safe or available.

Conflicts return to FAS-015 and the Executive. The Runtime never quietly steals
an active printer or configuration.

## Dispatch and state

Before dispatch, the Runtime verifies context state and identity, Executive
authority, resolved healthy provider, active resource leases, command expiry,
verification gates, and current operational state. `dispatched` means only
that a provider accepted a command request—not that physical work succeeded.

Contexts move through created, preparing, ready, running, waiting, paused,
recovering, verifying, and terminal states. Transitions record trigger and
authority. Terminal states release active leases.

## Interruption, compensation, and restart

Multi-step changes define compensation or rollback and disclose irreversible
work before start. Pause/cancel behavior is capability-specific; a generic
pause never assumes every device can stop safely.

After process or host restart, physical work never resumes blindly. FORGE
checks persisted context, leases, provider and hardware state, configuration,
safety, and fresh authority. A complete recovery assessment makes work only
eligible for Scheduler resumption; it does not start execution directly.

## First-release boundary

v1 implements one local node, user-requested Mission contexts, exclusive
printer/configuration locks, expiring leases, authorized local-provider
dispatch, safe restart handling, and structured progress/error/recovery
records. Distributed execution and autonomous multi-printer control remain
future-gated.

## Reference implementation and acceptance

`src/forge/fas/runtime.py` implements context validation and inheritance,
leases, conflicts, renewal/expiry, state transitions, guarded dispatch,
restart assessment, resource release, history, and health. Schemas/examples
must validate; children cannot broaden authority; incompatible leases block;
expiry enters recovery; dispatch requires all gates; restarts never blindly
resume physical work; and the complete FAS suite must pass.

## Decisions needed

None. Execution Contexts, expiring resource protection, and restart safety were
previously approved.
