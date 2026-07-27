# Isolated Slicer Worker Boundary

The worker manifest defines the Gate 4 isolation contract. Production and twin
workers receive separate input, output, and log workspaces and explicit
timeout, memory, and disk limits. Cancellation and crash recovery are part of
the worker supervisor, not the slicer engine.
Requests must declare an ephemeral profile. Successful result contracts must
carry a lowercase SHA-256 artifact digest; failed, cancelled, or timed-out
results cannot claim an artifact. Runtime validation and the published JSON
Schemas enforce the same rule.

Workspace paths are canonical relative POSIX paths under one dedicated worker
root. Absolute paths, drive paths, backslashes, empty components, `.`/`..`
aliases, nested production/twin roots, and request inputs outside the assigned
input directory are rejected before assignment.
Successful pair outcomes preserve their assigned workspaces. Preflight resolves
each output beneath a caller-supplied, non-symlinked execution root and rejects
artifacts outside the assigned output directory before reading their bytes.
Reads are capped by the assigned worker disk limit and rejected if file
identity, size, or modification time changes during hashing.
Pair composition accepts only the complete supervisor outcome shape. Success
and failure reasons, artifact acceptance, retry, cleanup, reuse, and authority
flags must be internally consistent; unknown fields cannot cross the boundary.
The pair assignment is also fully revalidated at composition: engine and input
digests, profile binding, worker identities and contexts, single-use flags,
limits, authority denials, and non-overlapping workspaces must all still match.

The worker must declare `printer_control` among its forbidden capabilities.
Printer discovery, cloud access, upload, update, telemetry, and print-start
paths are outside the worker contract. The worker returns evidence and derived
artifacts; FORGE authorization and the mandatory final user confirmation stay
in the Executive/runtime path.

Every manifest must uniquely declare all five forbidden capability classes:
printer control, printer discovery, cloud access, telemetry, and self-update.
Unknown fields, duplicate declarations, and any positive hardware-control
claim are rejected rather than silently rewritten.

This manifest is a contract-only artifact. It does not authorize Orca source
import or a production build while Gate 1 remains open.

Cross-platform process fixtures now exercise clean exit, non-zero crash,
timeout termination, and explicit cancellation against the supervisor. These
tests launch no slicer and grant no authority. A production launcher, operating
system sandbox, enforced memory/disk limits, and reviewed Orca process evidence
remain open.
