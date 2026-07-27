# FAS-034 - Print Execution and Job Lifecycle

Status: Implemented reference baseline
Version: 1.0.0
Historical source: FAS-033

FAS-034 defines the user-controlled print job state machine. A job must pass
preflight, reach readiness, receive three preparation clicks, and then require
a distinct fourth click: final confirmation. Final confirmation also requires
fresh live checks and verified authorization.
Job and actor identities are required to be non-empty strings before lifecycle
state can be recorded.

The reference implementation records transitions but does not upload, start,
or control a printer. Those side effects remain behind FAS-022 runtime, FAS-028
transport, and the production four-click interface integration.
