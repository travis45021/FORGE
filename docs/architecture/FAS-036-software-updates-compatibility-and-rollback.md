# FAS-036 - Software Updates, Compatibility, and Rollback

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-035

FAS-036 defines update manifests, digest identity, runtime compatibility,
verified backup and test gates, explicit user approval, and rollback planning.
The reference manager never installs, restarts, or grants physical execution
authority. Versions are validated as advancing numeric dotted values, digests
are strict SHA-256 values, and rollback versions must precede the target.
Production packaging may add installation effects only behind these gates.
