# OrcaSlicer Engineering Spike Plan

Status: Gate 2 preparation; source import blocked by Gate 1

This plan defines the smallest evidence-producing engineering spike for the
approved Orca-derived foundation. It does not authorize source import, public
distribution, printer discovery, cloud access, upload, or print start.

## Required boundary

The eventual worker must be an ephemeral, headless-capable process with:

- an explicit input directory and output directory;
- separate production and twin workspaces;
- resource, timeout, cancellation, and crash limits;
- deterministic request/result metadata and digests;
- no direct printer discovery or printer-control authority; and
- no Bambu networking, cloud, telemetry, updater, or upload path in the
  trusted worker graph.

## Evidence sequence after Gate 1

1. Reproduce the pinned unmodified build in isolated evidence storage.
2. Map slicer-core, GUI, profiles, networking, update, telemetry, and printer
   boundaries.
3. Select and document the smallest maintainable headless worker boundary.
4. Measure deterministic output, startup, memory, disk, and cancellation on
   STEP and 3MF fixtures.
5. Prove production and twin workers use one maintained engine codebase with
   independent state and cannot grant physical authority.

Until Gate 1 closes, this document is planning evidence only and the trusted
FORGE tree remains contract-only.
