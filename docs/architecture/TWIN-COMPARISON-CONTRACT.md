# Production/Twin Comparison Contract

The twin comparison records the shared input digest, both slicer results,
observable differences, and a user review status. A comparison may be
matching, different, inconclusive, or rejected; none of these states grants
production authority.

Production and twin workers must use isolated workspaces and preserve their
own provenance. Differences must be explainable or remain an explicit warning.
The comparison contract requires `can_authorize_production: false`; only the
governed Mission path and final user confirmation can authorize physical work.
