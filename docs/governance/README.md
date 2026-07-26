# FORGE Governance and Conversation Reference

This directory makes prior FORGE production conversations and approved decisions
referencable without treating chat text as executable authority.

## Start here

1. `FORGE-DECISION-REGISTER.md` — consolidated approved product and architecture
   decisions, current status, and precedence.
2. `FORGE-CHAT-PROVENANCE.md` — index of the source conversations, thread IDs,
   scope, and historical role.
3. `FORGE-PRODUCTION-ROADMAP.md` — canonical FAS-001–037 numbering, delivery
   order, release relevance, and historical reconciliation.
4. `fas-reconciliation-map.json` — machine-readable historical-to-production
   identifier mapping.
5. `FORGE-SLICER-LICENSING-INTEGRATION-TODO.md` — ordered compliance,
   architecture, integration, interface, and release gates for the approved
   OrcaSlicer-derived foundation.
6. `../architecture/ADR-001-orcaslicer-slicing-foundation.md` — binding
   production/twin, four-click, format, licensing, and authority boundaries.

## Authority order

When sources disagree, use this order:

1. The Forge Constitution.
2. Specifications and code committed to `travis45021/FORGE` on `main`.
3. Explicit approved decisions in the decision register.
4. Historical architecture files and project-board entries.
5. Conversation summaries and exploratory proposals.

Chat proposals are not automatically approved decisions. A later explicit
decision supersedes an earlier proposal. Current repository contracts supersede
historical FAS numbering when the same number was reused.
