# FORGE

FORGE is an open, capability-based 3D-printing control and assurance platform.
It is designed to support known and user-defined printers, components,
materials, accessories, and automation without redesigning the core for every
new device.

The current production baseline contains:

- **FAS-001:** Constitutional Governance Foundation
- **FAS-002:** Stable Kernel Architecture
- **FAS-003:** Capability Framework
- **FAS-004:** Mission Framework
- **FAS-005:** Forge Executive
- **FAS-006:** Forge Event System
- **FAS-007:** Decision Ledger and Evidence Architecture
- **FAS-008:** Policy Decision and Authorization Engine
- **FAS-009:** Policy Bundle Governance
- **FAS-010:** Trust Framework, Identity, Signing, and Sentinel
- **FAS-011:** AI Council Architecture (future-gated)
- **FAS-012:** User Interaction, Suggestions, and Attention
- **FAS-013:** Knowledge Core and Operational Memory
- **FAS-018:** Verification, Validation, and Assurance

FAS-001 through FAS-006 were reconstructed from approved project decisions
and the dependency contracts already published by FAS-007 and FAS-008. Each
specification identifies its reconstruction status.

FAS-008 includes a deterministic reference evaluator under
`src/forge/fas/authorization.py`. It is an authorization component, not a
printer-control service.

FAS-009 adds an immutable, content-addressed bundle registry and governed
activation/rollback reference component under
`src/forge/fas/policy_bundles.py`.

FAS-010 adds deterministic trust verification, immutable key lineage,
revocation, signed approvals, and a non-authoritative Sentinel evidence
boundary under `src/forge/fas/trust.py`.

FAS-011 is architecturally recognized but deliberately future-gated.

FAS-012 adds AI-free and suggestion-free defaults, attention budgets,
deduplication, dismissal, quiet hours, and strict separation between
interaction preferences and automation authority under
`src/forge/fas/interactions.py`.

FAS-013 adds evidence-backed local knowledge, explicit uncertainty, user
correction and supersession, dependency invalidation, advisory shared
knowledge, and deterministic export under `src/forge/fas/knowledge.py`.

FAS-018 adds contextual Verification Packets, scaled A0-A4 gates, explicit
claim states, separate authority verification, measured outcomes, and a
future-gated A5 boundary under `src/forge/fas/assurance.py`.

## Validation

Install the optional strict Draft 2020-12 schema validator:

```bash
python -m pip install -e ".[validation]"
```

Run the complete FAS test suite:

```bash
python -m unittest discover -s tests/fas -p "test_*.py" -v
```

The validator is intentionally optional: FORGE runtime components use only the
Python standard library, while validation and development environments can
enable strict schema and format checks through the `validation` extra.
