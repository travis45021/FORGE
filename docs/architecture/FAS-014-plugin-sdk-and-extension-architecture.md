# FAS-014 - Plugin SDK and Extension Architecture

Status: Production specification  
Version: 1.0.0  
Historical source: FAS-013  
Depends on: FAS-002, FAS-003, FAS-005 through FAS-010, FAS-013, FAS-018

## Principle and boundary

Plugins adapt the world to FORGE. Printers, custom components, transports,
services, interfaces, knowledge providers, Mission templates, and AI providers
integrate through documented capabilities rather than kernel modifications.
Installation, manufacturer identity, or AI generation never grants trust,
permission, authority, or capability availability.

## Manifest and lifecycle

Every plugin declares stable publisher-namespaced identity, semantic version,
API compatibility, type, capabilities, limitations, permissions, services,
isolation, network scope, configuration schema, validation tests, experimental
state, and execution gate.

Lifecycle is discovered, manifest-validated, security-checked,
dependency-resolved, configured, capability-validated, ready, active, and then
possibly degraded, disabled, quarantined, or retired. Every transition is
explained and event-recorded.

## Least privilege and capability registration

Plugins receive only declared and granted services and permissions. Undeclared
permissions are rejected. Capability declarations name operations, versions,
provider identity, limitations, and the permission each capability needs.
Only a ready plugin with Executive authorization may activate. Provisional
providers may exist and be tested but do not resolve as trusted production
capabilities.

Partial capability support is valid. FORGE reports the exact unavailable
operation rather than rejecting an entire custom device.

## Custom and unknown hardware

The no-code path collects only category, connection mapping, declared
operations, safe limits, validation procedure, and local evidence. It creates a
least-privilege provisional local manifest without guessing a manufacturer or
enabling unknown functions. Custom hardware needs no community approval for
local testing and never requires kernel changes when existing capability
contracts can represent it.

## Security and experimental gates

Separate-process isolation is preferred. Reduced isolation is labeled.
Failures degrade only affected capabilities. Simulation, AI-generated hardware
control, firmware flashing, new safety-sensitive capabilities, and autonomous
physical recovery remain simulation or test-hardware gated until validated.
Simulation output is prediction or simulated evidence, never physical proof.

## Updates, knowledge, and shared services

Updates revalidate manifests, signatures/checksums where available, permission
changes, capabilities, migrations, warnings, and rollback. New sensitive
permissions require explanation and authorization. Plugins may propose
knowledge but cannot silently replace user-verified local knowledge. Shared
indexes are optional; local plugins work offline.

## Reference implementation and acceptance

`src/forge/fas/plugins.py` implements manifest validation, lifecycle,
least-privilege grants, contract-test gates, trust-aware capability
registration, Executive activation, quarantine, and no-code custom manifests.
Schemas/examples must validate; unknown hardware must work without allowlists;
installation must not grant trust; permission expansion and namespace
impersonation must fail; provisional providers must not resolve as trusted; and
the complete FAS suite must pass.

## Decisions needed

None. First-release SDK scope, experimental gates, and local custom hardware
were previously approved.
