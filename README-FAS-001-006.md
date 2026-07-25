# FAS-001 through FAS-006 reconstruction package

This package restores the missing foundation beneath the validated FAS-007 and
FAS-008 baseline:

- constitutional governance and authority hierarchy;
- stable hardware-neutral kernel boundary;
- capability contracts and deterministic provider resolution;
- mission definitions and lifecycle enforcement;
- the Forge Executive orchestration gate;
- versioned event envelopes and idempotent consumption.

The reconstruction uses approved prior project decisions as normative anchors.
Details required for compatibility with FAS-007 and FAS-008 are explicitly
derived from those published contracts.

Run validation:

```bash
python -m unittest discover -s tests/fas -p "test_*.py" -v
```
