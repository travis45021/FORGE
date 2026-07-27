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

The Executive and Runtime independently preserve and verify this lineage.
Expiry is fail-closed: the upload command cannot outlive any evidence it
depends on. Upload permission does not start the print, and each published
evidence record explicitly carries `can_upload: false` and
`can_start_print: false` where those fields apply.

## Public adapter contracts

Replaceable printer adapters use the following strict, non-authoritative
evidence envelopes:

- [live-printer check schema](../../schemas/fas/live-printer-check-evidence.schema.json)
  and [example](../../examples/fas/live-printer-check-evidence.example.json);
- [final-confirmation schema](../../schemas/fas/final-confirmation-evidence.schema.json)
  and [example](../../examples/fas/final-confirmation-evidence.example.json);
- [provider-dispatch schema](../../schemas/fas/provider-dispatch-evidence.schema.json)
  and [example](../../examples/fas/provider-dispatch-evidence.example.json).

Their SHA-256 digests make silent mutation detectable. Schema validity and a
matching digest establish record integrity, not physical authority.

This contract is independent of the Orca integration and remains binding for
any future engine or printer capability provider.
