# OrcaSlicer v2.3.2 Header Scan

Status: Preliminary marker scan; Gate 1 remains open  
Recorded: 2026-07-26

This report records a read-only scan of an isolated extraction of the pinned
OrcaSlicer archive. The extracted copy is outside the trusted FORGE tree and
is not part of the FORGE distribution.

## Results

- Candidate text/source files scanned: **13,982**
- Files containing an SPDX marker (`SPDX-License-Identifier` or
  `SPDX-FileCopyrightText`): **301**
- Files containing a case-insensitive `copyright` marker: **2,188**
- Files containing a broader license/copyright marker scan: **2,075**

The scan also surfaced many dependency headers under `deps_src/`, confirming
that the archive's license obligations cannot be inferred from the root
`LICENSE.txt` alone.

## Interpretation and limits

These are marker counts, not a completed SPDX inventory. They do not classify
each file, resolve conflicting or inherited notices, identify generated files,
prove build/runtime reachability, or determine whether any component is
compatible with a FORGE integrated distribution. The scan also does not prove
that the optional non-free Bambu networking component is absent from every
graph.

Next evidence requires file-level classification, dependency/build graph
review, exclusion proof, and legal/compatibility review. Gate 1 therefore
remains active.
