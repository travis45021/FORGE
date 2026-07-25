# FAS-008 production package

This package extends the validated FAS-007 baseline with the Forge Policy
Decision and Authorization Engine:

- production architecture specification and acceptance criteria;
- policy, authorization request, and authorization result schemas;
- capability-based examples for user-directed print authorization;
- deterministic, side-effect-free Python reference evaluator;
- authorization behavior and schema tests.

Run all available FAS validation from the repository root:

```bash
python -m unittest discover -s tests/fas -p "test_*.py" -v
```

The evaluator and behavior tests use only the Python standard library. Schema
tests use `jsonschema` when it is installed.

The reference evaluator authorizes only. It does not control a printer or
replace production identity, signature, persistence, event, or Sentinel
services.

