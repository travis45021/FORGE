# FORGE v1 Assurance Matrix

Status: Planned evidence matrix; execution remains open

| Area | Required evidence | Release assertion blocked until |
| --- | --- | --- |
| Input security | Hostile and malformed STEP/3MF fixtures, including path traversal | Quarantine rejects or safely contains every fixture |
| Worker resilience | Crash, timeout, cancellation, memory, disk, and stale-context scenarios | Supervisor produces deterministic terminal evidence |
| Reproducibility | Source/profile/input digests and deterministic output comparison | Repeated real-engine runs produce explainable matching results; the non-authoritative comparison evaluator is implemented |
| Twin separation | Twin output, replay, and comparison attempts | No twin or replay path grants production authority |
| Four-click authority | UI, API, automation, and recovery-path scenarios | No path skips the final **Yes, Print** action |
| Hardware neutrality | Known, custom, unavailable, unhealthy, untrusted, and mismatched capability scenarios | The reference registry returns plain-language, capability-first limits and safe next steps without a brand allowlist |
| Release integrity | Notices, source match, SBOM, excluded components, signatures | CI verifies wheel Python byte-for-byte against published source; the complete release evidence set remains open |
| Accessibility | Equivalent keyboard, assistive, and plain-language workflows | Core workflow remains usable without hidden bypasses |

The matrix is a planning artifact. Passing individual tests cannot close Gate 1
or FAS-037 without the complete evidence package and final human release
decision.
