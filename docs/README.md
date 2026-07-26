# FORGE Documentation Map

The Constitution is the highest project authority. The folders below separate
normative architecture, governance history, compliance evidence, and
implementation release notes so their roles are not confused.

## Folders

- `architecture/` contains normative FAS specifications and approved
  architecture decision records.
- `governance/` contains the production roadmap, decision register,
  conversation provenance, reconciliation map, integration worklists, and
  readiness audits.
- `compliance/` contains licensing and upstream provenance evidence. Evidence
  here does not itself complete a legal or release gate.
- `releases/` contains historical implementation-package notes. These notes
  describe what entered the reference baseline; they do not override current
  specifications or prove v1 product readiness.

Schemas live in `../schemas/fas`, matching examples in `../examples/fas`,
reference components in `../src/forge/fas`, and verification in
`../tests/fas`.

## Authority

Use this order when documents disagree:

1. `../CONSTITUTION.md`
2. Current FAS specifications and approved ADRs
3. Approved entries in the decision register
4. Versioned schemas and public contracts
5. Reference implementation and tests
6. Historical release notes and conversation provenance
