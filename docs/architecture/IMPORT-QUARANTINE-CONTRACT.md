# STEP/3MF Import and Quarantine Contract

Every supported STEP or 3MF input is first represented by an
[import assessment](../../schemas/fas/import-assessment.schema.json). The
assessment records the source digest, isolated quarantine status, hostile-file
and path-traversal checks, user-resolution ambiguities, and the accepted or
rejected decision.

An accepted assessment is not a print authorization. Normalization, slicing,
Mission creation, live printer checks, upload, and the final **Yes, Print**
confirmation remain separate governed steps. A twin assessment cannot grant
production authority.
