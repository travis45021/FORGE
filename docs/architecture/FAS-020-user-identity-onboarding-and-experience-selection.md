# FAS-020 - User Identity, Onboarding, and Experience Selection

Status: Production specification  
Version: 1.0.0  
Historical source: FAS-019  
Depends on: FAS-008 through FAS-010, FAS-012 through FAS-015, FAS-018, FAS-019

## Principle

The user chooses FORGE's role. FORGE follows that choice. A local display
identity and fully local operation require no cloud account, community
membership, manufacturer approval, AI provider, or known-hardware preset.

## v1 experience profiles

FORGE v1 exposes only:

- **Offline and Manual:** no network, AI, or unsolicited suggestions.
- **Simple Local:** local-first guided setup with AI and suggestions off.
- **Custom Builder:** no-code custom hardware, explicit limits and validation,
  with AI and suggestions off.

Assisted, Supervised Automation, and Autonomous Path remain future-gated until
their evidence and safety release gates are met. A5 is never exposed as a
promise or hidden control.

## Composable choices and authority

Experience profiles are editable setting bundles, not personas, tiers, or
paywalls. Network participation, AI, suggestions, explanation surfaces,
Operational Twin visibility, hardware setup, notifications, and data sharing
remain individually understandable. Capability existence, interface visibility,
and execution authority are separate. Experience changes cannot expand
automation authority; authority changes use their own verified governance path.

## Local identity, privacy, and custom hardware

Local identity and optional network identity are separate. Shared services
require explicit consent and a separate identity. Declining sharing never
blocks local history, deterministic safety, Missions, configuration, logs,
health, custom hardware, or the Operational Twin. Every supported component
category offers an honest Custom path without programming.

## Transparency and reversibility

The user can always inspect a concise effective summary: network, AI,
suggestions, hardware path, automation, and Operational Twin state. Settings
can change without reinstalling or discarding unrelated local work. Disabling
AI or reducing authority takes effect promptly.

## Reference implementation and acceptance

`src/forge/fas/onboarding.py` implements local identity, the three v1 profiles,
future-profile gates, composable settings, explicit shared-service consent,
separate authority handling, export, event history, and transparency summaries.
Schemas/examples must validate; local identity must need no network account;
future profiles must fail closed; Custom Builder must be AI-free; experience
changes must not expand authority; sharing needs consent; and the complete FAS
suite must pass.

## Decisions needed

None. Local identity, the narrowed v1 profile set, and autonomy honesty were
previously approved.
