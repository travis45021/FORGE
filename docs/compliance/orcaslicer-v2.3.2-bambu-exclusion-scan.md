# OrcaSlicer v2.3.2 Bambu Exclusion Scan

Status: Exclusion not established; Gate 1 remains open  
Recorded: 2026-07-26

## Read-only archive findings

The pinned archive's member names contain **1,035** broad Bambu/network/cloud
markers. Most are Bambu printer/material profiles and related assets. More
importantly, the archive contains these explicit Bambu networking source/test
members:

- `src/slic3r/Utils/BBLCloudServiceAgent.cpp`
- `src/slic3r/Utils/BBLCloudServiceAgent.hpp`
- `src/slic3r/Utils/BBLNetworkPlugin.cpp`
- `src/slic3r/Utils/BBLNetworkPlugin.hpp`
- `src/slic3r/Utils/bambu_networking.hpp`
- `tests/libslic3r/test_bambu_networking.cpp`

This is not evidence that FORGE must ship those components. It is evidence
that a simple filename-absence assertion is invalid and that the integrated
distribution needs an explicit build, packaging, runtime, update, and test
graph exclusion proof. Bambu profiles and images also require a separate
asset/trademark and redistribution review.

## Gate consequence

The Bambu exclusion row remains open and is now a known audit risk. No Orca
source has been imported into the trusted FORGE tree, and no integrated public
distribution is authorized by this scan.
