# OrcaSlicer v2.3.2 License Compatibility Notes

Status: Preliminary evidence; no final legal determination  
Recorded: 2026-07-26

Representative license texts were read directly from the pinned archive in
read-only mode:

- OrcaSlicer root: GNU AGPL version 3.
- MCUT: a mutually exclusive GPL option and commercial option; the archived
  `LICENSE.GPL.txt` is GNU GPL version 3.
- Expat: permissive Expat license.
- ImGui: MIT license.
- Eigen: primarily MPL 2, with some BSD and LGPL-covered third-party code.

## Compatibility implications

The dependency set is mixed and includes strong copyleft, weak copyleft, and
permissive components. A public integrated FORGE distribution therefore needs
to preserve the applicable notices and corresponding-source obligations, and
must verify that the selected MCUT licensing path is documented and compatible
with the final FORGE license expression. A filename inventory or the Orca root
AGPL text alone is insufficient.

These notes do not determine whether every dependency is actually built or
shipped, do not resolve all transitive licenses, and do not constitute legal
advice. Build-graph reachability, full SPDX classification, notices, SBOM,
source-offer instructions, and qualified legal review remain required before
Gate 1 closure.
