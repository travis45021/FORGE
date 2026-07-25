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
