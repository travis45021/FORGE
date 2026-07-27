# FORGE v1 Threat Model

Status: Incomplete; security release gate not passed

FORGE protects user authority, local data, manufacturing artifacts, release
integrity, and physical hardware across untrusted file input, local interface,
slicer-worker, provider, packaging, and user-presentation boundaries.

The machine-readable
[`v1-threat-register.json`](v1-threat-register.json) records the current
threats, controls, evidence, residual risk, and release-blocking state. A
control is not treated as complete merely because a contract exists. Real
worker isolation, reviewed dependencies, complete release artifacts, and
hardware-in-the-loop evidence remain open and keep the security gate false.

The register is fail-closed:

- controlled threats require repository evidence;
- open or partially controlled threats state their residual risk;
- release-blocking threats cannot coexist with a passed security gate; and
- the register never authorizes a release or physical execution.

Future reviews must add new boundaries and threats rather than deleting open
risk without replacement evidence and a review record.

Both this explanation and the machine-readable register are exposed through
the local transparency catalog so users and release reviewers do not need a
cloud account or a hidden administrative path to inspect security status.
