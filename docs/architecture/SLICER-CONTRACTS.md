# FORGE Slicer Contracts

The [slicer request schema](../../schemas/fas/slicer-request.schema.json) and
[slicer result schema](../../schemas/fas/slicer-result.schema.json) define the
contract-only Gate 3 boundary.

Requests identify the quarantined STEP/3MF input, profile digest, production or
twin context, and the already-created Mission. Results preserve engine/source
provenance, warnings, output digest, and failure state. Both schemas make
physical authority explicit: a slicer result cannot upload or start a print.

These contracts do not import Orca source or authorize a worker build. They
remain subject to Gate 1 licensing, Gate 2 boundary evidence, and the
mandatory four-click user-confirmation path.
