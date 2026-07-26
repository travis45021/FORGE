# License Status

Status: Licensing direction approved; final repository grant pending audit  
Effective date: 2026-07-26

FORGE has approved GNU AGPL version 3 as the licensing direction for the
integrated application described by
`docs/architecture/ADR-001-orcaslicer-slicing-foundation.md`.

The repository does not yet make a final project-wide license grant. The exact
SPDX expression and file-level treatment must follow the copyright,
provenance, and compatibility audit in
`docs/governance/FORGE-SLICER-LICENSING-INTEGRATION-TODO.md`. Existing notices
continue to apply to code and materials that already carry them.

Until that gate is complete:

- do not describe the repository as fully relicensed;
- do not import Orca-derived source into the trusted production tree;
- do not distribute a public integrated binary or hosted integrated service;
- preserve all upstream and historical FORGE notices; and
- keep the optional non-free Bambu networking plugin outside the trusted
  baseline and packaging graph.

This software-license direction does not transfer ownership of user files,
profiles, local knowledge, evidence, or produced artifacts. Those remain
user-owned unless the user separately and explicitly shares them under chosen
terms.
