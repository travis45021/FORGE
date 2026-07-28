# FAS-031 - Material Handling and Extrusion Capability Design Review

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-030

FAS-031 reviews material profiles for feed range, feed and extrusion rate
limits, retraction behavior, jam response, sensor-fault response, and thermal
references. A successful review is accepted for integration review only; it
does not authorize extrusion or assert hardware safety.
Malformed material collections, provider identity, reviewer identity, and
non-UTC review timestamps are rejected before a review can be accepted;
malformed material values become deterministic findings.

Material-specific calibration, load testing, jam recovery, and hardware-
in-the-loop evidence remain required before physical dispatch.
