# FAS-015 - Mission Scheduling and Priority

Status: Production specification  
Version: 1.0.0  
Historical source: FAS-014  
Depends on: FAS-004 through FAS-010, FAS-012, FAS-013, FAS-018

## Principle and authority boundary

FORGE does the right authorized work at the right time for the right reason.
The Scheduler orders, waits, reserves, pauses, resumes, preempts, and completes
already-authorized Missions. Priority is never permission, and the Scheduler
has no hardware-command authority.

## Priorities and states

Priority classes are Background, Low, Normal, High, Critical, and Emergency.
Context may elevate urgency, but cannot expand authority. Scheduling states are
queued, waiting for approval/capability/resource/condition, scheduled, running,
paused, preempted, completed, cancelled, and failed. Every transition records a
plain-language reason.

## Readiness and resources

A Mission becomes ready only after approval, capability, dependencies,
conditions, AI preference, and exclusive resources are satisfied. Independent
resources may run in parallel. User attention is treated as a limited resource
under FAS-012; optional work cannot masquerade as urgent.

## Preemption and recovery

Preemption requires Executive authorization, policy allowance, a higher
priority, and a safe pause point. Emergency protection may override an ordinary
pause boundary, but not deterministic physical safety. Non-preemptible windows
are short and declared. Recovery and retries are bounded to prevent loops.

## Fairness, cost, and offline operation

Age may raise Background/Low/Normal work to High when safe, but never to
Critical or Emergency. Safety is not traded for cost. Deterministic local
analysis is preferred when it satisfies the Mission; AI work is scheduled only
when enabled and required. Ordinary local Missions continue offline.
Distributed scheduling remains future-gated.

## Reference implementation and acceptance

`src/forge/fas/scheduler.py` implements authorized submission, deterministic
priority/fairness, readiness explanations, resource reservations, safe
preemption, completion, bounded retry, and health reporting. Schemas and
examples must validate; unauthorized Emergency work must fail; conflicts must
block parallel use; AI-free waits must be explained; non-emergency preemption
must require safe pause; and the complete FAS suite must pass.

## Decisions needed

None. Priority classes, user attention as a resource, and the distributed
scheduling future gate were previously approved.
