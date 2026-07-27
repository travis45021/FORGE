# FAS-033 - Manufacturing Artifact, G-code, and Preflight

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-032

FAS-033 classifies uploaded manufacturing artifacts and records preflight
findings before slicing or printing. STEP and 3MF are the preferred v1 source
formats; STL remains accepted input. G-code may be inspected but is never
trusted as authority. F3D architecture is explicitly deferred.

The reference service verifies basic identity and digest shape, records caller-
provided validation checks, rejects symbolic-link inputs, and always requires
user review. It does not slice, upload, start, or authorize physical work.
