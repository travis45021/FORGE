# FAS-002 — Forge Stable Kernel Architecture

Status: Reconstructed production specification  
Version: 1.0.0  
Depends on: FAS-001  
Owner: Forge Assurance Services (FAS)

## 1. Purpose

FAS-002 defines the smallest stable, hardware-neutral FORGE kernel. New
printers, accessories, materials, slicers, models, and manufacturers must be
added through contracts and plugins, not kernel redesign.

## 2. Kernel-owned services

The kernel owns lifecycle and contracts for:

- Forge Runtime and Forge Executive;
- Event Bus and Service Manager;
- Plugin Loader and Capability Registry;
- Mission Scheduler and Decision Ledger;
- Configuration Manager and Trust Framework.

The kernel owns orchestration, identity, validation, isolation, routing,
version negotiation, and health. It does not own brand-specific behavior.

## 3. Excluded from the kernel

Printer drivers, G-code dialects, manufacturer rules, hardware profiles,
material profiles, camera models, AI providers, dashboards, mobile clients,
and community databases remain replaceable modules. A module communicates
through versioned capabilities and events and receives only explicit
permissions.

## 4. Lifecycle

Services move through `discovered`, `validated`, `registered`, `starting`,
`ready`, `degraded`, `stopping`, `stopped`, or `failed`. Dependencies form an
acyclic graph. Readiness is published only after required dependencies,
contracts, configuration, and trust checks pass. Shutdown proceeds in reverse
dependency order.

## 5. Boundary rules

- no service reaches hardware except through a granted capability operation;
- no plugin mutates another service's private state;
- configuration is versioned and validated before activation;
- missing required dependencies fail closed;
- optional failures produce explicit degraded state;
- capability identity describes behavior, never brand membership;
- public contracts support deterministic compatibility negotiation.

## 6. Acceptance criteria

A new user-defined printer can register capabilities without source changes to
the kernel. The kernel can reject incompatible contracts, start dependencies in
order, report degraded health, and stop services safely.
