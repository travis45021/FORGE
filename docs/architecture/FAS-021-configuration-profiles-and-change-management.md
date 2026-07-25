# FAS-021 - Configuration, Profiles, and Change Management

Status: Production specification

FORGE resolves profiles in this fixed order: safe defaults, machine/components,
material/process, validated calibration, Mission settings, and permitted user
changes. Later layers may specialize values but may never weaken hard safety
limits.

Profiles are versioned, provenance-backed, comparable, exportable, and
reversible. Safety-, hardware-, calibration-, and active-Mission-affecting
changes require a verified and authorized Change Request, a backup, and an
explicit rollback target. Material changes wait while a physical Mission is
active. Imported, community, and AI-authored profiles begin provisional and
cannot silently replace validated local configuration.

`src/forge/fas/configuration.py` implements deterministic layering, hard-limit
enforcement, immutable registration, material-change gates, active-Mission
protection, history, and authorized rollback.

## Decisions needed

None. Resolution order and reversible material-change governance were approved.
