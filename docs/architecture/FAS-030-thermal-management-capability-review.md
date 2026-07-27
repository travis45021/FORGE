# FAS-030 - Thermal Management Capability Design Review

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-029

FAS-030 reviews thermal zones for sensor identity, operating limits, control
mode, heating/cooling rate limits, overtemperature behavior, sensor-fault
behavior, and power interlocks. A successful review is accepted for
integration review only; it never asserts physical safety or authorizes heat.
Malformed zone collections, provider identity, reviewer identity, and non-UTC
review timestamps are rejected before a review can be accepted.

Provider calibration, independent safety cutoffs, thermal runaway testing, and
hardware-in-the-loop evidence remain required before physical dispatch.
