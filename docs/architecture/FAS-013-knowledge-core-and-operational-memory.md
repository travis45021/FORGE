# FAS-013 - Knowledge Core and Operational Memory

Status: Production specification  
Version: 1.0.0  
Historical source: FAS-012  
Depends on: FAS-001 through FAS-010 and FAS-012

## Purpose and authority boundary

FORGE remembers structured knowledge, not noise. The Knowledge Core stores,
organizes, retrieves, ages, and explains operational knowledge. It informs the
Executive but cannot authorize Missions, command hardware, override policy,
replace the Ledger, or convert confidence into authority.

## Invariants

1. Data, evidence, fact, user statement, measurement, inference, prediction,
   preference, policy reference, outcome, and unknown remain distinct.
2. Every item records scope, confidence, provenance, origin, state, timestamps,
   dependencies, verification need, and supersession links.
3. User-verified local knowledge is authoritative only for its installation.
4. Shared knowledge is advisory until explicitly adopted; adoption begins
   provisional unless separately verified.
5. AI may propose inference or prediction but cannot silently create an
   authoritative fact.
6. User corrections preserve prior context and cannot be silently overwritten
   by AI, plugins, imports, or community sources.
7. Dependency changes make affected knowledge stale and require revalidation.
8. Conflicting evidence is preserved and explained, not silently deleted.
9. Knowledge remains locally queryable and exportable without internet access.
10. High confidence does not grant execution authority.

## Object states and provenance

States are `provisional`, `active`, `stale`, `disputed`, `superseded`,
`retired`, `invalidated`, and `advisory`. State transitions record reason and
source. Safety-sensitive facts require stronger verification and conservative
fallbacks.

Source quality is evaluated separately from identity using directness,
repeatability, calibration, recency, integrity, compatibility, confirmation,
agreement, and conflict history. Branding, popularity, or confident AI tone do
not establish truth.

## Local, shared, and imported knowledge

Local operation and ownership are the default. Community sharing is optional,
granular, minimized, and consent-based. Imported data is schema-checked,
conflict-checked, provenance-labeled, and provisional unless it is a verified
local backup. Remote synchronization never silently replaces local knowledge.

## Corrections, aging, and digital twins

Corrections create a new object and supersede the prior object. Historical
Missions retain their original context. Aging and dependency triggers can mark
items stale without forcing intrusive suggestions; FAS-012 controls attention.

Digital twins initially represent structured state, relationships, evidence,
history, and health. They are not full physics simulations. Advanced simulation
remains experimental until validated.

## Privacy, retention, and export

FORGE stores only useful, explainable, authorized knowledge. Retention varies by
type and remains visible. Users may archive, redact, delete payloads, retain
minimal audit references, or fully delete where safe and lawful. Export uses
documented machine-readable formats and does not lock users into hidden storage.

## Reference implementation

`src/forge/fas/knowledge.py` provides immutable creation, provenance and AI
boundaries, explicit shared adoption, user correction and supersession,
dependency invalidation, query, explanation, deterministic export, and history.
It intentionally has no hardware-command or authorization API.

## Acceptance

Schemas and examples must validate; provenance is mandatory; shared and AI
knowledge cannot become truth silently; user corrections preserve history;
dependencies become stale after change; exports are complete; unknown hardware
identities work without manufacturer lists; and the complete FAS suite passes.

## Decisions needed

None. This ports approved provisions under the reconciled canonical number.
