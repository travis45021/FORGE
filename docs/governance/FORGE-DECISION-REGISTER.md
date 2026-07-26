# FORGE Production Decision Register

Status: Consolidated baseline  
Last consolidated: 2026-07-26
Repository baseline: `6ef08a1e95aaac73ba9f90da65b0daeda0855ce2`

## Interpretation rules

- `Approved` means the user explicitly approved the decision or approved all
  pending decisions before continuing.
- `Implemented` means the current production repository contains an executable
  or documented form of the decision.
- `Historical` means the decision remains useful but its original numbering or
  packaging was superseded.
- `Deferred` means intentionally excluded from the first production baseline.
- Exploratory assistant proposals are omitted unless the user adopted them.

## A. Constitutional and product identity

### FORGE-DEC-001 — Constitution is the highest authority

Status: Approved; Implemented

The Forge Constitution outranks specifications, engineering standards, APIs,
implementation documentation, source code, plugins, integrations, and profiles.
Convenience, popularity, commercial interest, and implementation difficulty do
not override it.

### FORGE-DEC-002 — Evidence and explanation before significant action

Status: Approved; Implemented

Significant recommendations and actions must be evidence-backed, explainable,
traceable, and honest about confidence, assumptions, limitations, and unknowns.
AI output is evidence, not authority.

### FORGE-DEC-003 — User authority

Status: Approved

Foundational interaction rule: **You decide. Forge follows.** Users may choose
manual, AI-free operation or explicitly delegate broader automation. FORGE may
not silently expand its authority. Delegation must remain scoped, revocable,
auditable, and bounded by safety and policy.

### FORGE-DEC-004 — Local-first and optional cloud

Status: Approved

Core FORGE operation and core data remain usable locally without a cloud
account. Cloud, community, distributed compute, shared evidence, and remote
interfaces are optional and consent-based.

### FORGE-DEC-005 — Open, documented, and inspectable

Status: Approved

Core work should be open source whenever practical. Documentation is part of
the software. Meaningful behavior must be traceable and inspectable. Open
interfaces are required; closed ecosystems are rejected.

### FORGE-DEC-006 — Licensing requires an explicit release decision

Status: Historical; Superseded by FORGE-DEC-077

AGPLv3 was originally identified as a strong candidate because network-served
modifications remain open. The licensing direction has now been approved by
FORGE-DEC-077, while its exact SPDX expression and compliance packaging remain
blocked on the recorded provenance audit.

## B. Architecture and extensibility

### FORGE-DEC-010 — Stable, hardware-neutral kernel

Status: Approved; Implemented

New printers, accessories, components, and providers should integrate through
capabilities, plugins, services, Missions, and configuration rather than kernel
changes. Stable layers depend on abstractions, not manufacturers.

### FORGE-DEC-011 — Capability-first hardware model

Status: Approved; Implemented

FORGE verifies capability contracts, compatibility, limits, permissions, and
behavior—not brands. Capability identifiers describe universal behavior.
Capabilities are composable, versioned, self-describing, and self-validating.

### FORGE-DEC-012 — Unknown and custom hardware is first-class

Status: Approved; Implemented in foundational contracts

Real users must be able to add custom printers, hotends, extruders,
multimaterial systems, sensors, and controllers without coding or kernel edits.
The no-code custom path declares only the minimum capabilities, limits,
connection details, and validation state. Unknown functions remain unavailable
until declared and validated, with a plain-language explanation.

### FORGE-DEC-013 — K1 Max is the first reference, not a platform limit

Status: Approved

The 2025 K1 Max and local Moonraker/Klipper workflow are the first validated
reference integration. FORGE Core remains printer-neutral, and custom
controllers remain supported through replaceable providers and provisional
capability mappings.

### FORGE-DEC-014 — Capability Design Review before implementation

Status: Approved

Every new capability category must be reviewed for composability, unknown
hardware, custom implementations, validation, and kernel independence before
code is written.

### FORGE-DEC-015 — Missions are the unit of meaningful work

Status: Approved; Implemented

FORGE executes outcome-oriented Missions, not uncontextualized commands.
Mission transitions, authority, evidence, capability requirements, recovery,
and results are recorded.

### FORGE-DEC-016 — Executive is authoritative but not AI or a driver

Status: Approved; Implemented

The Executive coordinates and authorizes significant work. It does not perform
AI inference or directly control hardware. Hardware commands flow through
authorized Missions and capability providers.

### FORGE-DEC-017 — Events do not grant authority

Status: Approved; Implemented

Events report facts. Requests propose evaluation. Decisions record conclusions.
Commands are authorized instructions. Historical replay cannot re-execute
physical work without a newly authorized Mission.

## C. Trust, security, policy, and evidence

### FORGE-DEC-020 — One AI Council with specialist evidence roles

Status: Approved; Historical architecture

Use one flexible AI Council rather than separate voting councils. Members submit
evidence and confidence, not simple votes. Sentinel is a specialist security
member but may not become an unrestricted authority.

### FORGE-DEC-021 — Sentinel blocks and quarantines; it does not silently delete

Status: Approved

Sentinel may report, block execution, quarantine, disable, or request approval
within declared security authority. Actions must be visible and recorded.
Deterministic emergency protections may take narrowly defined immediate safety
actions and must report them immediately.

### FORGE-DEC-022 — Signed integrity with user-modified builds allowed

Status: Approved concept; production mechanism incomplete

Official releases, bundles, dependencies, and sensitive distributed events
should support signatures and integrity verification. Locally modified builds
must be described honestly rather than prohibited merely for differing from an
official signature. Key rotation and revocation are required production topics.

### FORGE-DEC-023 — Append-only decision evidence

Status: Approved; Implemented in FAS-007

Decision Records are append-only and tamper-evident, using hash chaining and
signed checkpoints. Decision Records are permanent; bulky evidence may use
policy-controlled retention. Community evidence sharing is opt-in.

### FORGE-DEC-024 — Deterministic policy authorization

Status: Approved; Implemented in FAS-008

Authorization evaluates actor, role, scope, action, capability, Sentinel state,
approval requirements, ledger integrity, denies, and automation limits.
High-privilege administration remains restricted. Unknown hardware remains
capability-based.

### FORGE-DEC-025 — Policy bundles are immutable and governed

Status: Approved; Implemented in FAS-009

Policy bundles are canonical, content-addressed, signed, immutable after
registration, and activated atomically by channel. Activation and rollback
require Forge Admin authority, verified approvals, clear Sentinel state,
constitutional compatibility, intact ledger/registry state, and exact lineage.
Rollback preserves history and targets a registered ancestor.

### FORGE-DEC-026 — Policy failure restricts new authority, not safe continuity

Status: Approved concept

Loss of central policy evaluation must block new significant or unverified
actions while allowing monitoring, deterministic safety, controlled completion
inside the last verified envelope, safe pause/shutdown, and recovery. Future
deployments should use signed local policy snapshots, expiration, redundancy,
and failover tests.

## D. User experience, modes, and automation

### FORGE-DEC-030 — Suggestions must respect attention

Status: Approved

Simple Mode defaults to AI-free and optional-suggestion-free operation.
Suggestion preferences are separate from automation authority. Optional
suggestions have attention budgets, deduplication, and permanent dismissal.
Warnings, critical alerts, and required approvals remain distinct.

### FORGE-DEC-031 — Onboarding is local and choice-driven

Status: Approved; v1 scope later narrowed

Users can start with a local display name and no online account. Historical
onboarding profiles were Offline and Manual, Simple Local, Custom Builder,
Assisted, Supervised Automation, and Autonomous Path. These are editable
starting profiles, not locked tiers.

### FORGE-DEC-032 — v1.0 exposes only baseline modes

Status: Approved

FORGE v1.0 exposes Offline and Manual, Simple Local, and Custom Builder.
Assisted, supervised, and autonomous release interfaces wait until the platform
has sufficient evidence, validation, and safety maturity. Long-term autonomy
remains a goal.

### FORGE-DEC-033 — Automation classes A0–A5

Status: Approved architecture; A5 deferred

- A0: Informational.
- A1: Low-impact guidance.
- A2: Operational recommendation.
- A3: Controlled action.
- A4: Safety-critical action.
- A5: Full delegated autonomy.

A5 is a transparent, reserved future class—not a hidden backdoor. It requires
explicit revocable delegation, continuous verification, limits, safe recovery,
local stop, and full audit history.

### FORGE-DEC-034 — No “irrefutable fact” claims

Status: Approved

Even with a large evidence base, real-world manufacturing conclusions retain
scope, assumptions, uncertainty, and revalidation conditions. Observations,
hypotheses, tested possibilities, verified recommendations, authorized actions,
and measured outcomes must remain visibly distinct.

## E. Knowledge, data, community, and AI

### FORGE-DEC-040 — Local knowledge belongs to the user

Status: Approved

User-verified local knowledge is authoritative for that installation. Shared or
community knowledge is advisory until explicitly adopted. User corrections may
not be silently overwritten by AI, plugins, imports, or community data.

### FORGE-DEC-041 — Community sharing is opt-in and granular

Status: Approved

New installations share no data or artifacts by default. Community profiles
require explicit adoption and cannot silently replace active safety limits or
configuration. Safety-critical community guidance requires stronger validation
and is never automatically applied.

### FORGE-DEC-042 — Distributed FORGE remains locally sovereign

Status: Approved; Deferred beyond v1

Distributed nodes may optionally contribute evidence, testing, database
building, research, or bounded compute under visible limits for privacy, power,
money, bandwidth, storage, and schedule. Remote nodes cannot control local
hardware without explicit local acceptance and enforcement.

### FORGE-DEC-043 — AI is selective, replaceable, and cost-aware

Status: Approved

Routine known work should become deterministic and inexpensive. Stronger AI is
used selectively for unknowns, difficult planning, diagnosis, or review.
FORGE must not depend on one AI provider, and ordinary local control must work
without AI.

### FORGE-DEC-044 — Long-term additive-manufacturing autonomy

Status: Approved long-term goal; Deferred

The north star is a human-standard intended result: users can eventually provide
an F3D/G-code or equivalent manufacturing intent and FORGE can inspect, prepare,
configure, execute, monitor, recover, and learn with minimal intervention.
Automatic slicing, autonomous file optimization, and AI-assisted/generated
toolpaths are long-term goals subject to verification and authority boundaries.

## F. Digital twin, configuration, runtime, and operations

### FORGE-DEC-050 — Digital Twin v0.1 is an Operational Twin

Status: Approved

The first twin represents known state, history, limits, relationships, active
Mission, measurements, verification status, warnings, recovery, and decision
basis. It is not a full physics simulator and does not expose private
chain-of-thought.

### FORGE-DEC-051 — Advanced simulation is gated

Status: Approved; Deferred

Advanced simulation remains behind developer, testing, or explicit experimental
gates until its scope and accuracy are validated. Simulation is evidence and
cannot authorize real hardware action by itself.

### FORGE-DEC-052 — Configuration is explainable and reversible

Status: Approved

Profile resolution order is safe defaults → machine/components →
material/process → validated calibration → Mission settings → permitted user
changes. Safety-, hardware-, calibration-, and active-Mission-affecting changes
require a verified Change Request, backup, and rollback path. AI-authored or
autonomous configuration waits for its release gate.

### FORGE-DEC-053 — Runtime uses recorded execution contexts and leases

Status: Approved

Meaningful Mission actions run inside recorded Execution Contexts containing
authority, policy, configuration, verification, capability, and resource
references. Incompatible resources use reservations/locks with expiring leases.
Physical work is never blindly resumed after restart.

### FORGE-DEC-054 — Health is multi-state and recovery is narrow

Status: Approved

Health distinguishes healthy, unobserved, stale, degraded, unavailable, failed,
and recovering. Recovery starts with the smallest safe scope. v1 automatic
recovery is limited to deterministic, nonphysical, low-risk actions.

### FORGE-DEC-055 — Local data backup cannot replay hardware

Status: Approved

Core data is local by default. v1 includes manual backup/restore, integrity
checks, portable import/export, and backups before material changes or
migrations. Restore cannot replay historical commands or blindly resume an
interrupted physical Mission.

## G. Interfaces, hardware, and print lifecycle

### FORGE-DEC-060 — All interfaces share the Executive path

Status: Approved

Local UI, CLI, APIs, and future interfaces use the same Executive evaluation
path for significant actions. No interface directly controls hardware.
Accessibility is a first-release requirement.

### FORGE-DEC-061 — Connection details are not machine identity

Status: Approved

SSID, IP address, hostname, USB path, and similar details are mutable connection
information, not permanent printer identity.

### FORGE-DEC-062 — Motion and thermal safety are composable

Status: Approved; FAS-028/FAS-029 flagged for later reread

Motion distinguishes commanded, reported, and verified position. Thermal
functions use named thermal zones. FORGE cannot weaken or bypass deterministic
local motion/thermal protections. Autonomous tuning and optimization are
excluded from v1.

### FORGE-DEC-063 — Material systems are capability-composed

Status: Approved

Sources, feeders, sensors, selectors, extruders, and tool changers remain
separate composable capability families. Partial systems report precisely what
is missing. v1 focuses on verified single-material workflows and
user-requested calibration.

### FORGE-DEC-064 — Vision is optional evidence

Status: Approved

Cameras and AI vision are optional, local-first, and privacy-controlled.
Vision output is evidence with confidence and limitations, never proof or
direct control authority. v1 requires no vision AI.

### FORGE-DEC-065 — G-code is an artifact, not permission

Status: Approved

Import and analysis do not start a print, modify profiles, upload content, or
invoke AI automatically. G-code receives deterministic preflight and explicit
profile/context binding. Unknown commands are flagged. Authorized advanced
users retain a clearly labeled unverified raw-command path that cannot bypass
physical safety.

### FORGE-DEC-066 — v1 print lifecycle is explicitly user-started

Status: Approved

Every v1 print starts from a direct user request after artifact preflight and
live preparation checks. Controller-reported completion is not automatically a
verified manufactured outcome. v1 has no autonomous start, resume, parameter
modification, or physical fault recovery.

### FORGE-DEC-067 — Sensors are optional context

Status: Approved

Environment, power, enclosure, door, smoke, UPS, and similar sensors are
optional composable context. FORGE may observe and report physical safety
systems but cannot weaken, override, mask, or automatically reset them.

### FORGE-DEC-068 — Updates are user-controlled and separate from firmware

Status: Approved

Updates are local-first, stageable, user-controlled, reversible where
practical, and support offline import. Material updates wait for inactive
physical Missions unless the user accepts a safe interruption. Firmware flashing
and printer configuration changes are separate high-assurance, user-requested
Missions.

## H. v1 scope and engineering process

### FORGE-DEC-070 — v1 succeeds for one local user first

Status: Approved

FORGE v1.0 is a dependable local baseline that remains valuable even if no
community ecosystem emerges. It prioritizes stability, transparency,
custom-hardware support, data building, manual/Builder workflows, and the K1 Max
reference integration.

### FORGE-DEC-071 — Architecture before feature volume

Status: Approved

Engineering follows requirement review, architecture validation,
implementation, tests, replay validation where applicable, documentation, and
release assurance. A feature is not done merely because it appears to work.

### FORGE-DEC-072 — Major updates end with user decisions

Status: Approved user preference

Major FORGE responses should end with a concise section containing only the
items that require the user's approval, rejection, modification, or attention.

## I. Integrated slicing and licensing

### FORGE-DEC-073 — OrcaSlicer is the slicing foundation

Status: Approved; Integration gated

FORGE will use OrcaSlicer as its upstream slicing foundation while remaining a
broader manufacturing control and assurance platform. FORGE continues to own
Objects, Builder flows, Missions, authority, verification, Runtime, the
Operational Twin, and learning. The slicer is a governed capability and cannot
command hardware or authorize physical work.

### FORGE-DEC-074 — One engine runs in production and twin contexts

Status: Approved; Integration gated

FORGE will maintain one Orca-derived engine codebase with isolated production
and twin execution contexts, not two divergent forks. The production context
creates a candidate manufacturing artifact. The twin context creates advisory
toolpath evidence. Only the Executive and Runtime may move an accepted artifact
into an authorized capability-provider path.

### FORGE-DEC-075 — v1 uses a mandatory four-click print path

Status: Approved

The v1 path is: add the design file, confirm inferred or selected context,
create the verified Print Mission, then choose **Yes, Print** after live printer
checks and before controlled upload or start. A future bypass structure may be
represented, but it is disabled for every v1 user, role, and mode.

### FORGE-DEC-076 — STEP and 3MF are the first design inputs

Status: Approved

Integrated design-file preparation begins with STEP and 3MF. Full F3D project
architecture is deferred. Imported G-code remains a preflighted manufacturing
artifact rather than a design source that FORGE must slice.

### FORGE-DEC-077 — GNU AGPL version 3 is the licensing direction

Status: Approved direction; Compliance gate open

The integrated FORGE application adopts GNU AGPL version 3 as its licensing
direction. A file-level copyright, provenance, and compatibility audit must
decide the exact `AGPL-3.0-only` versus `AGPL-3.0-or-later` SPDX expression and
complete notices, corresponding-source, SBOM, and release obligations before a
public integrated release. Existing upstream notices and the MIT notices on any
reused historical FORGE bootstrap code must be preserved.

The software license does not transfer ownership of user design files,
profiles, local knowledge, evidence, or produced artifacts. User data remains
user-owned unless explicitly shared under separately chosen terms.

### FORGE-DEC-078 — Non-free networking is outside the trusted baseline

Status: Approved

The optional non-free Bambu networking plugin is excluded from the trusted
FORGE build, packaging graph, and required operating path. Printer connectivity
uses governed, replaceable capability providers and may not become a vendor
lock-in boundary.

## Known reconciliation items

1. Historical FAS-007–036 documents exist in a prior project workspace, while
   the current repository implements a production FAS-001–009 sequence with
   different numbering from historical FAS-009 onward.
2. Historical FAS-009 Policy/Authority Governance maps conceptually to current
   production FAS-008 Authorization Engine plus FAS-009 Policy Bundles.
3. Historical FAS-010 AI Council has no current production-number assignment.
4. The full historical FAS-010–036 set should not be copied into current
   `docs/architecture` without a formal renumbering and reconciliation pass.
5. GNU AGPL version 3 is the approved integrated-app licensing direction. The
   exact SPDX expression and release compliance package remain pending the
   file-level audit.

## Reconciliation status

Completed in `FORGE-PRODUCTION-ROADMAP.md` and
`fas-reconciliation-map.json`.

The next canonical specification is FAS-027 — Executive Lifecycle and Service
Management. The production reference baseline is implemented through FAS-026,
excluding intentionally future-gated FAS-011,
FAS-016, and FAS-017. Historical FAS-009 is absorbed by current production
FAS-008/FAS-009; historical FAS-010–036 map to canonical FAS-011–037.
