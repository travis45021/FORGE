# FORGE v1 Four-Click Print Contract

The v1 print path has four distinct user actions:

1. **Add file** — place a STEP, 3MF, or other supported input into quarantine.
2. **Confirm context** — accept or correct inferred printer, material, process,
   and safety context.
3. **Create verified Print Mission** — review validation, twin evidence,
   warnings, and limitations, then create the Mission.
4. **Yes, Print** — after live printer checks and immediately before controlled
   upload/start, explicitly authorize physical execution.

The fourth action is mandatory in v1 and cannot be delegated, hidden, merged,
or satisfied by a slicer result, simulation, historical replay, API call, or
background automation. A failed or stale live check returns the Mission to a
non-authorized state and requires the user to review again.

## Evidence chain

Click three records the named reviewer, review time, immutable comparison
digest, accepted artifact digest, input and profile digests, and exact slicing
engine source and build digests. Click four is valid only when:

- the complete live-printer check record passes and is no more than five
  minutes old;
- the user explicitly confirms the same job and evidence lineage;
- the confirmation follows the click-three review and live checks;
- the confirmation is no more than ten minutes old; and
- the final provider health, state, and upload-capability evidence is no more
  than thirty seconds old at Runtime dispatch.

Live-check records accept exactly the six named provider-neutral checks as
explicit booleans. Unknown fields, non-boolean values, invalid provider
identity, non-UTC timestamps, and validity windows over five minutes are
rejected before evidence is created.
The final-confirmation presenter recomputes the complete evidence digest and
requires presentation time to fall between the recorded check and expiry.
Mutated, future-dated, expired, contradictory, or extra-field evidence cannot
show **Yes, Print**. A recorded click carries the live-evidence digest and
expiry forward without dispatching hardware.

The Executive and Runtime independently preserve and verify this lineage.
Expiry is fail-closed: the upload command cannot outlive any evidence it
depends on. Upload permission does not start the print, and each published
evidence record explicitly carries `can_upload: false` and
`can_start_print: false` where those fields apply.

Final provider-dispatch evidence accepts exactly three boolean checks, exact
provider/context/capability identity, UTC timestamps, and no more than thirty
seconds of validity. Runtime rejects unknown top-level fields even when a
caller recomputes the evidence digest, so secret or contradictory data cannot
be smuggled through the final provider envelope.

## Public adapter contracts

Replaceable printer adapters use the following strict, non-authoritative
evidence envelopes:

- [live-printer check schema](../../schemas/fas/live-printer-check-evidence.schema.json)
  and [example](../../examples/fas/live-printer-check-evidence.example.json);
- [final-confirmation schema](../../schemas/fas/final-confirmation-evidence.schema.json)
  and [example](../../examples/fas/final-confirmation-evidence.example.json);
- [fourth-click presentation-record schema](../../schemas/fas/fourth-click-presentation-record.schema.json)
  and [example](../../examples/fas/fourth-click-presentation-record.example.json);
- [provider-dispatch schema](../../schemas/fas/provider-dispatch-evidence.schema.json)
  and [example](../../examples/fas/provider-dispatch-evidence.example.json).

Their SHA-256 digests make silent mutation detectable. Schema validity and a
matching digest establish record integrity, not physical authority.

## Application composition

`forge.fas.print_dispatch.PrintDispatchCoordinator` is the reference
application composition boundary. It invokes the Executive, replaceable
transport registry, and Runtime in that order. Any rejection stops the chain.
Its result distinguishes an upload command accepted by Runtime from an actual
print start or confirmed physical outcome; both remain false.

The coordinator has no network or device client and cannot bypass the
underlying gates. A product-facing application may call it only after creating
the Mission, acceptance, authorization, fourth-click receipt, active Runtime
lease, and fresh provider evidence required by those services.

The raw confirmation token and complete internal confirmation receipt are
passed only between the transport and Runtime guards. They are not returned to
the application caller. The caller receives the non-secret evidence digests,
lineage, attribution, validity windows, and dispatch result needed to explain
the outcome.

This contract is independent of the Orca integration and remains binding for
any future engine or printer capability provider.
