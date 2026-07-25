# FORGE

FORGE is an open, capability-based 3D-printing control and assurance platform.
It is designed to support known and user-defined printers, components,
materials, accessories, and automation without redesigning the core for every
new device.

The current recovered production baseline contains:

- **FAS-007:** Decision Ledger and Evidence Architecture
- **FAS-008:** Policy Decision and Authorization Engine

FAS-008 includes a deterministic reference evaluator under
`src/forge/fas/authorization.py`. It is an authorization component, not a
printer-control service.

## Validation

```bash
python -m unittest discover -s tests/fas -p "test_*.py" -v
```

Schema tests require the optional `jsonschema` package. All reference evaluator
behavior tests use only the Python standard library.

