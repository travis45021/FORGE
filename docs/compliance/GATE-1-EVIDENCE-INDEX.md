# Gate 1 Evidence Index

Status: Active; no Orca source imported
Owner: FORGE release maintainer

This index is the controlled checklist for the first open release gate. A row
may move to **complete** only when the linked artifact is present, hashed, and
reviewed. This document does not make a licensing determination.

| Evidence area | Required artifact | Current status |
| --- | --- | --- |
| Upstream pin | tag, commit, source URL, archive digest | Pin, digest, and isolated archive retention verified |
| License inventory | file-level headers and SPDX report | Preliminary isolated header-marker scan recorded; classification incomplete |
| Dependency inventory | libraries, assets, profiles, translations, generated content | Archive member/dependency-tree inventory recorded; audit incomplete |
| Compatibility | AGPL/GPL/permissive compatibility analysis | Not started |
| Exclusions | proof Bambu networking is absent from all graphs | Not started |
| FORGE provenance | historical MIT reuse and notices audit | Not started |
| Project license | final `AGPL-3.0-only` or `AGPL-3.0-or-later` decision | Pending evidence/legal review |
| Notices | root license, NOTICE, third-party notices | Not started |
| Source offer | corresponding-source and publication instructions | Not started |
| SBOM | machine-readable release dependency inventory | Not started |
| Contributor terms | DCO/inbound/trademark rules | Not started |
| Privacy | user ownership and opt-in sharing terms | Not started |
| Legal review | qualified review record | Required before public integrated release |
| Automation | release checks for notices, source match, exclusions, SBOM | Not started |

The trusted repository remains contract-only until the index's applicable rows
are complete. Gate 1 cannot be closed by tests that do not inspect the pinned
upstream source and release artifacts.
