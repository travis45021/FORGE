# FORGE v1 Slicer Integration Support, Limitations, Rollback, and Recovery

Status: Pre-release contract baseline  
Effective date: 2026-07-26  
Public distribution cleared: No

## Supported upstream baseline

FORGE pins OrcaSlicer release `v2.3.2` at source commit
`c724a3f5f51c52336624b689e846c8fbc943a912`. This identifies the only upstream
baseline currently under review. It does not mean an Orca-derived engine,
binary, or hosted service has been integrated, built, tested, or approved for
distribution.

Gate 1 licensing, provenance, notice, corresponding-source, SBOM, exclusion,
and qualified legal-review requirements remain release blockers. Until they
close, the trusted repository contains FORGE contracts and reference services,
not Orca-derived source.

The v1 integrated input direction is STEP/STP and 3MF. Full F3D project support
is deferred. G-code may be governed as an already-derived artifact in a future
path; it is not an input to the current integrated slicing contract.

## Current known limitations

- No Orca-derived worker is present in the trusted production tree.
- No reproducible unmodified or integrated Orca build has passed Gate 2.
- No engine-backed geometry normalization or hostile-geometry fixture suite
  has been completed.
- No real production/twin engine processes run yet. Current isolation,
  comparison, cancellation, timeout, crash, and resource-limit behavior is a
  tested FORGE reference contract.
- No application shell renders the four print screens yet.
- No real Moonraker/Klipper or other printer adapter has passed
  hardware-in-the-loop testing. Moonraker/Klipper is a reference provider, not
  a compatibility boundary.
- No public integrated installer, binary, hosted service, or complete
  corresponding-source release is approved.
- Root licensing, final notices, final SBOM, and policy documents remain
  audit- or legal-review dependent.
- The two existing pytest collection warnings for assurance service class
  names are non-failing but should be removed before release-candidate signoff.

## Rollback requirements

An integrated release may activate only when the previous verified FORGE
package, configuration, profiles, policy set, and migration state are available
as a rollback target. Rollback must be explicit, attributable, and user-visible.
It must never silently broaden authority or substitute an older approval.

Rollback procedure:

1. Block new slicing and physical dispatch.
2. Safely stop and isolate production and twin workers.
3. Mark in-flight artifacts untrusted for dispatch; do not reuse confirmation
   tokens or live-check evidence.
4. Preserve logs, decisions, digests, warnings, and failure evidence.
5. Restore the last verified package and its compatible configuration from a
   verified backup.
6. Run package integrity, schema, configuration, provider, and health checks.
7. Keep affected Missions paused until the user reviews recovery.
8. Require fresh slicing evidence, live printer checks, authorization, and the
   mandatory fourth **Yes, Print** click before any physical continuation.

If the prior verified state cannot be restored and validated, FORGE remains
paused. It must not fall forward to an unverified package.

## Recovery requirements

Worker crash, timeout, cancellation, memory exhaustion, disk exhaustion, or
stale context produces fail-closed terminal evidence. The worker workspace is
cleaned, its artifact is rejected, and that worker instance is not reused.
Retry requires a fresh execution context.

Application or host restart must not replay upload or print commands. Restored
records are review evidence only. Physical work may resume only after provider
state, hardware state, safety, authority, and resource leases are freshly
verified.

Recovery never treats twin output as physical proof, never converts historical
confirmation into current authority, and never bypasses the four-click path.

## Release evidence required to remove this pre-release status

- Gate 1 evidence and signed qualified legal review;
- reproducible pinned-upstream and integrated builds;
- complete source, notices, source offer, and SBOM matching shipped artifacts;
- proof that excluded non-free components are absent from the build graph;
- production/twin isolation and determinism measurements;
- hostile geometry and real worker fault tests;
- application accessibility and workflow-parity conformance;
- hardware-in-the-loop evidence for at least one replaceable provider;
- installer, upgrade, rollback, and crash-recovery exercises; and
- FAS-025 release-assurance approval.
