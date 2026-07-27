# FORGE Unified UX Requirements

FORGE presents one integrated interface. Users do not need to open a separate
slicer application or write code to use supported or custom hardware.

## Required flow

- **Step 1 — Add file:** accept STEP/3MF first, show quarantine and format
  status, and explain unsupported or unsafe input plainly.
- **Step 2 — Confirm context:** show inferred printer capabilities, material,
  process, and safety context; let the user correct or define custom hardware
  through guided no-code controls.
- **Step 3 — Create Mission:** show validation, twin comparison, warnings,
  limitations, and provenance before creating the verified Print Mission.
- **Step 4 — Yes, Print:** show live printer checks and require the explicit
  final confirmation immediately before controlled upload/start.
- **After click four — Dispatch status:** distinguish the upload command being
  sent from printer receipt, print start, and confirmed physical outcome.
  Until provider evidence proves those later states, show them as unconfirmed
  and keep the print-start control disabled. The public contract is the
  [dispatch-status schema](../../schemas/fas/dispatch-status-presentation.schema.json)
  with a matching [example](../../examples/fas/dispatch-status-presentation.example.json).

Unavailable capabilities must be explained in plain language with next steps.
The UI must never imply that an inferred brand profile is a compatibility
boundary or that simulation evidence is physical proof. Accessibility,
structured errors, equivalent core workflows, license/source access, privacy,
and data export are first-release requirements.

The shared interface boundary rejects confirmation tokens, full final-
confirmation evidence, private keys, and generic secret fields at any nesting
depth. It also requires readable labels and unique action identifiers before a
screen can reach any interface mode.

These requirements are contract-only until Gate 1 and the implementation gates
are complete.
