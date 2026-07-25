# FAS-018 - Verification, Validation, and Assurance

Status: Production specification  
Version: 1.0.0  
Historical source: FAS-017  
Depends on: FAS-001 through FAS-010, FAS-012, FAS-013

## Core rule

FORGE may hypothesize freely. It must verify before it recommends with
confidence, authorizes action, or claims an outcome. Verification supplies an
honest evidence basis; it never replaces user authority.

## Claim states

`observation`, `hypothesis`, `candidate`, `tested`,
`verified_recommendation`, `authorized_action`, and `measured_outcome` are
visibly distinct. Model tone, popularity, branding, or confidence cannot
promote a claim between states.

## Context and packets

Verification applies only to a fingerprinted context. Packets record the
subject, claim state, assurance class, required/completed/failed/waived checks,
evidence, assumptions, uncertainties, applicability limits, confidence,
verifier versions, expiry, revalidation triggers, and governed waiver.
Hardware, firmware, plugin, profile, sensor, material, environmental, or failed
outcome changes may expire applicability.

## Assurance classes

- **A0:** informational source and timestamp.
- **A1:** low-impact guidance with context and applicability.
- **A2:** operational recommendation with capability, compatibility, evidence,
  and recovery.
- **A3:** controlled action with authority, live state, safety, monitoring, and
  A2 checks.
- **A4:** safety-critical action with deterministic safety, strong evidence,
  explicit constraints, and conservative authorization.
- **A5:** reserved future delegated autonomy. It is not a v1 control or hidden
  authority path.

Consequences determine class. AI confidence does not.

## Gates and authority

Checks fail closed with an explicit incomplete, blocked, limited, defer, or
verified result. Verification of a recommendation does not authorize execution.
An authorized action requires both A3/A4 verification and a separately verified
FAS-008 authority decision. Safety-critical checks and constitutional
restrictions cannot be waived.

## Validation and outcomes

When evidence is incomplete, FORGE prefers a small bounded validation Mission
with limits, stop conditions, measurements, success criteria, and recovery.
High-impact claims seek genuinely independent corroboration where practical.
Measured outcomes require evidence and are compared with the prediction.
Failure protects people/equipment, invokes authorized recovery, records the
discrepancy, reduces applicability where justified, and triggers revalidation.

## AI and digital twins

AI and twin outputs remain hypotheses outside validated scope. A verified
recommendation requires current local context, applicable model scope,
acceptable calibration, evidence, and the assurance-class checks. Private
reasoning is not required; claims, evidence, assumptions, limits, and outcomes
are inspectable.

## Reference implementation and acceptance

`src/forge/fas/assurance.py` implements canonical context fingerprints,
class-specific minimum gates, expiry, failures, governed waivers, authority
separation, the A5 gate, and measured outcomes. Schemas/examples must validate;
context drift and failed checks must block; A4 safety checks cannot be waived;
outcomes require evidence; and the complete FAS suite must pass.

## Decisions needed

None. Claim language, scaled A0-A5 assurance, the twin boundary, and A5 future
gate were previously approved.
