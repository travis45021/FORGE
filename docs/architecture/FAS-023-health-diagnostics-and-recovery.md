# FAS-023: Health, Diagnostics, and Recovery

Status: Implemented baseline  
Historical source: FAS-022

FORGE reports health as evidence, not a guess. The common contract records the
object checked, explicit state, observation time, freshness window, confidence,
check type, evidence, reason codes, and affected capabilities.

The canonical states are `healthy`, `unobserved`, `stale`, `degraded`,
`unavailable`, `failed`, and `recovering`. Expired observations become stale;
absence of current evidence is never presented as healthy.

Diagnostics preserve the difference between evidence and an unconfirmed causal
hypothesis. Dependency analysis identifies direct impact without declaring
unrelated objects unhealthy.

Recovery starts with the smallest safe scope. FORGE v1 may automatically approve
only deterministic, nonphysical, low-risk actions. Physical or higher-risk
recovery requires explicit Executive authority and safety verification. Every
plan has a positive attempt limit, repeated failures suppress further retries,
and recovery becomes healthy only after evidence-backed verification.

The reference service records health and recovery events but exposes no hardware
command surface. Deterministic safety systems remain independently authoritative
for immediate protective action.
