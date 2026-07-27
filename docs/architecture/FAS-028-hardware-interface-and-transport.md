# FAS-028 - Hardware Interface and Transport

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-027

FAS-028 defines a capability-first provider boundary for custom, off-brand,
and user-built hardware. Providers advertise transport identity, health, and
capabilities; FORGE does not maintain a fixed printer whitelist.
Provider identities, capability lists, and health observations are validated
before registration or state changes, including strict UTC observation
timestamps.

The reference registry discovers providers, records health, rejects raw
hardware commands, and prepares structured commands only when authorization,
verification, an active runtime lease, and fresh user confirmation are all
present. It deliberately does not dispatch physical work. FAS-022's runtime
dispatcher and the later print lifecycle remain the only path to execution.

Moonraker/Klipper may be the first tested provider, but it is not a hardware
compatibility boundary. OrcaSlicer remains a separate slicing foundation and
does not receive transport authority.
