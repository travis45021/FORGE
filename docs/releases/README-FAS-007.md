# FAS-007 production package

This package adds the Forge Decision Ledger and Evidence Architecture:

- `docs/architecture/FAS-007-decision-ledger-and-evidence-architecture.md`
- `schemas/fas/decision-record.schema.json`
- `schemas/fas/evidence-record.schema.json`
- `schemas/fas/ledger-amendment.schema.json`
- `examples/fas/decision-approved.example.json`
- `examples/fas/evidence-bed-selection.example.json`
- `tests/fas/test_fas_007_schemas.py`
- `tests/fas/test_fas_007_integrity.py`

Run validation from the repository root:

```bash
python -m unittest discover -s tests/fas -p "test_fas_007_*.py" -v
```

The schema tests use `jsonschema` when installed. Integrity tests use only the
Python standard library.
