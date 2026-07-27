# Gate 1 Evidence Index

Status: Active; no Orca source imported
Owner: FORGE release maintainer

The decision-ready owner and counsel packet is
[`GATE-1-LICENSING-DECISION-PACKET.md`](GATE-1-LICENSING-DECISION-PACKET.md).
It records conservative recommendations, unresolved questions, required legal
deliverables, and closure criteria without making a legal determination.

This index is the controlled checklist for the first open release gate. A row
may move to **complete** only when the linked artifact is present, hashed, and
reviewed. This document does not make a licensing determination.

| Evidence area | Required artifact | Current status |
| --- | --- | --- |
| Upstream pin | tag, commit, source URL, archive digest | Pin, digest, and isolated archive retention verified |
| License inventory | file-level headers and SPDX report | Preliminary isolated header-marker scan recorded; classification incomplete |
| Dependency inventory | libraries, assets, profiles, translations, generated content | 55 dependency roots and profile/asset inventory recorded; classification incomplete |
| Compatibility | AGPL/GPL/permissive compatibility analysis | Preliminary representative-license notes recorded; full compatibility review open |
| Exclusions | proof Bambu networking is absent from all graphs | Preliminary scan found explicit Bambu networking source; exclusion proof required |
| FORGE provenance | historical MIT reuse and notices audit | Conversation/decision provenance indexed; file-level MIT reuse audit incomplete |
| Project license | final `AGPL-3.0-only` or `AGPL-3.0-or-later` decision | Owner confirmed `AGPL-3.0-only`; evidence/legal compatibility review open |
| Notices | root license, NOTICE, third-party notices | Draft NOTICE added; final notices and root license remain open |
| Source offer | corresponding-source and publication instructions | Draft SOURCE-OFFER added; release offer remains open |
| SBOM | machine-readable release dependency inventory | Preliminary JSON baseline added; complete SPDX/SBOM remains open |
| Contributor terms | DCO/inbound/trademark rules | Draft CONTRIBUTING.md and TRADEMARKS.md added; legal review/finalization open |
| Privacy | user ownership and opt-in sharing terms | Draft PRIVACY.md and USER-DATA-TERMS.md added; legal review/finalization open |
| Legal review | qualified review record | Open; unsigned record requires completion before v1 public integration |
| Automation | release checks for notices, source match, exclusions, SBOM | Baseline script and CI workflow added; full release checks remain open |

The trusted repository remains contract-only until the index's applicable rows
are complete. Gate 1 cannot be closed by tests that do not inspect the pinned
upstream source and release artifacts.
