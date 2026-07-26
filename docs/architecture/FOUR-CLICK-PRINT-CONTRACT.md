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

This contract is independent of the Orca integration and remains binding for
any future engine or printer capability provider.
