# FAS-035 - Environment, Power, and Safety Sensors

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-034

FAS-035 reviews environmental and safety sensors for normal ranges, trip and
loss behavior, and an independent safety path. It covers power-loss and
environmental constraints as evidence-bearing capability declarations.

The review is not a safety certification and does not authorize physical
execution. Independent electrical, thermal, and hardware-in-the-loop testing
remain required before a production release claims these capabilities.
Malformed sensor collections, provider identity, reviewer identity, and
non-UTC review timestamps are rejected before a review can be accepted;
malformed safety values become deterministic findings. This capability remains
optional for v1.
