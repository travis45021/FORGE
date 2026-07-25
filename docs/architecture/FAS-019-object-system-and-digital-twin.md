# FAS-019 - Object System and Digital Twin

Status: Production specification  
Version: 1.0.0  
Historical source: FAS-018  
Depends on: FAS-002, FAS-003, FAS-006 through FAS-010, FAS-013, FAS-014, FAS-018

## Principle

FORGE understands a workshop through connected objects rather than
manufacturer-specific settings pages. Objects, relationships, capabilities,
evidence, operational state, health, limits, and policy are separate concepts.
Unknown information remains explicit instead of being replaced with guesses.

## Common object model

Every physical, material, configuration, Mission, capability, software,
evidence, or environment object has an immutable internal identity, namespaced
type, editable display name, owner scope, lifecycle and knowledge state,
version, capabilities, state, health, limits, policies, provenance, metadata,
unknown fields, creation source, timestamps, and reason.

Lifecycle describes representation maturity; operating state describes what is
happening now. Health, limits, and permission remain distinct.

## Relationships and history

Relationships are typed, directed, scoped, evidence-backed, version-aware
facts—not permanent inferences from temporary proximity. Object changes create
new inspectable versions and event history rather than erasing significant
context. Degradation affects dependent capabilities and Missions, not unrelated
objects.

## Custom hardware

No-code Custom Hotend, Extruder, Nozzle, Sensor, Camera, or material system
creates the same base object as known hardware. It retains the honest custom
display identity, declared capabilities and limits, provisional lifecycle,
source provenance, validation needs, and unknown/unavailable functions without
inventing manufacturer identity.

## Digital Twin v0.1

The baseline twin is an optional, user-enabled Operational Twin showing known
objects, relationships, capabilities, live state, measurements, health, limits,
evidence, unknowns, active Mission context, warnings, recovery, and decision
basis. It is not a physics simulator, authority source, proof of safety, or
private chain-of-thought surface. Simulation remains experimentally gated and
its output remains evidence under FAS-018.

## Reference implementation and acceptance

`src/forge/fas/objects.py` provides immutable identity, versioned evidence-backed
updates, typed relationships, graph queries, isolated health impact, and the
opt-in Operational Twin v0.1 snapshot. Schemas/examples must validate; custom
identity and unknowns must remain honest; categories must stay separate;
history must persist; relationships need evidence; twin output must be
non-simulated and non-authoritative; and the complete FAS suite must pass.

## Decisions needed

None. The common model, honest custom identity, and Operational Twin v0.1 scope
were previously approved.
