# FAS-029 - Motion and Positioning Capability Design Review

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-028

FAS-029 defines the evidence-bearing review contract for motion providers.
Each axis must declare units, travel limits, velocity and acceleration limits,
homing requirements, limit behavior, and fault behavior. A review can accept a
contract for integration review, but never asserts physical safety or grants
execution authority. Malformed axis collections, provider identity, reviewer
identity, and non-UTC review timestamps are rejected before findings are
produced.

The review is capability-first and hardware-neutral. Provider-specific testing,
calibration, collision clearance, and hardware-in-the-loop evidence remain
required before physical dispatch.
