# FAS-012 - User Interaction, Suggestions, and Attention

Status: Production specification  
Version: 1.0.0  
Historical source: FAS-011  
Depends on: FAS-001 through FAS-010  
Future-gated dependency: FAS-011 AI Council is not required

## 1. Foundation

> You decide. Forge follows.

FAS-012 defines how FORGE communicates without becoming intrusive, coercive,
AI-dependent, or accidentally authoritative. The user controls communication,
recommendation, and interruption choices. Interaction settings never grant
automation authority.

## 2. Required invariants

1. A personal installation defaults to Simple interaction, AI disabled,
   optional suggestions disabled, and manual automation.
2. AI-free operation retains deterministic safety, capabilities, missions,
   configuration, diagnostics, automation explicitly created by the user, and
   operational explanations.
3. Suggestion-free operation retains status, approvals, warnings, critical
   alerts, outcomes, and requested help.
4. Optional suggestions obey category choices, deduplication, dismissal,
   quiet hours, and attention budgets.
5. A permanent dismissal may be revisited only after materially new evidence
   or an explicit user request.
6. Required approvals, warnings, and critical alerts are never disguised as
   suggestions and do not consume suggestion budgets.
7. Critical alerts may bypass quiet hours only for narrowly defined immediate
   safety, security, or damage conditions.
8. No interaction setting may increase automation authority.
9. AI output receives no extra prominence merely because AI produced it.
10. FORGE does not optimize for engagement, notification opens, time in the
    interface, or increased automation.

## 3. Interaction classes

Every user-facing interaction is exactly one of:

- `status`: current operation; no attention required;
- `information`: useful context that may wait;
- `suggestion`: optional improvement;
- `approval_request`: authorization is required before proceeding;
- `warning`: material concern requiring consideration;
- `critical_alert`: immediate safety, security, or Mission risk;
- `outcome`: result of an authorized action or completed Mission.

Classes cannot be relabeled to gain attention.

## 4. Profiles

- **Quiet:** essential approvals, warnings, and critical alerts only.
- **Simple:** concise status and outcomes; AI and suggestions off by default.
- **Guided:** limited relevant suggestions and setup guidance.
- **Proactive:** broader timely suggestions, still attention-bounded.
- **Managed:** organization-defined routing and escalation.

Profiles are editable starting points. Communication profile and automation
profile are separate fields and separate authority domains.

## 5. User intent record

The exportable local record includes:

- interaction profile;
- AI enabled/disabled;
- suggestions enabled/disabled;
- automation profile reference;
- per-day and per-Mission suggestion limits;
- disabled categories;
- quiet hours.

Reset returns communication to conservative Simple defaults without silently
changing the automation profile.

## 6. Suggestion eligibility

A suggestion must name its subject, source class, category, evidence, expected
benefit, confidence, urgency, deduplication identity, and available user
actions. It is eligible only when:

- allowed by the current interaction policy;
- supported by evidence;
- not a duplicate of an active suggestion;
- not permanently dismissed for the same evidence state;
- outside any reminder cooldown;
- within daily and Mission attention budgets;
- timed outside quiet hours unless directly requested.

Requested assistance bypasses optional proactive-delivery suppression and
ordinary suggestion budgets. It does not bypass AI-disablement when the
requested response would require an AI provider.

## 7. Dismissal and repetition

Supported dismissal modes include permanent dismissal and a time-bounded
reminder. Permanent dismissal is keyed by suggestion equivalence and evidence
digest. A materially different evidence digest permits renewed evaluation;
FORGE must explain the changed evidence in the presentation layer.

Permanent opt-out controls must remain visible and understandable.

## 8. Attention and timing

Ordinary unsolicited suggestions consume both the per-day budget and, when
applicable, the per-Mission budget. Requested help does not consume either.
Related nonurgent suggestions should be grouped by presentation services while
preserving individual evidence and dismissal controls.

Quiet hours defer information, suggestions, warnings, status, and nonurgent
outcomes. Time-sensitive approvals and critical alerts may be exempt according
to explicit policy.

## 9. Notification and accessibility boundary

Notification channels are replaceable capabilities. No external channel is
required for local operation. External notifications minimize sensitive
content and remain permission-bound.

All production interfaces must support plain language, keyboard operation,
screen readers, color-independent severity, adjustable text, reduced motion,
localization, and user-selected units. FAS-024 defines the complete interface
and accessibility contract.

## 10. Failure behavior

If interaction delivery fails:

- deterministic safety and physical emergency controls remain active;
- critical conditions use an available authorized fallback;
- new approval-dependent actions pause;
- autonomous actions continue only within existing authorization;
- records queue locally when possible;
- the system exposes a visible degraded state.

## 11. Events and evidence

Initial event families include:

- `interaction.profile.changed`
- `interaction.preferences.reset`
- `suggestion.presented`
- `suggestion.dismissed`
- `suggestion.expired`
- `notification.delivered`
- `notification.failed`
- `approval.presented`
- `warning.presented`
- `critical_alert.presented`

Material suggestions, permanent dismissals, authority changes, AI preference
changes, approval responses, and critical delivery results integrate with
FAS-007. Ordinary views need not become permanent decisions.

## 12. Reference implementation

`src/forge/fas/interactions.py` supplies deterministic preference management,
delivery classification, quiet hours, AI and category gates, suggestion
budgets, deduplication, dismissal, evidence-sensitive repetition, and an
inspectable history. Durable storage, channel delivery, localization, grouping
UI, and concurrent transactional enforcement remain adapter responsibilities.

## 13. Acceptance criteria

FAS-012 is accepted when:

1. schemas and examples validate under JSON Schema Draft 2020-12;
2. Simple defaults are AI-free and suggestion-free;
3. essential alerts survive suggestion suppression;
4. interaction changes cannot expand automation authority;
5. budgets, quiet hours, deduplication, and dismissal are deterministic;
6. new evidence can reopen a permanently dismissed recommendation;
7. requested assistance remains available without enabling proactive delivery;
8. unknown/community hardware identifiers remain supported;
9. the complete FAS suite passes.

## Decisions needed

None. This specification implements previously approved provisions and keeps
future AI Council operation outside the v1 baseline.
