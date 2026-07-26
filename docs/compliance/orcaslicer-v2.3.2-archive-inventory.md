# OrcaSlicer v2.3.2 Archive Inventory

Status: Initial filename inventory; Gate 1 remains open  
Recorded: 2026-07-26

## Scope and provenance

This is a read-only inventory of the exact pinned archive retained outside the
trusted FORGE repository. It does not import Orca source, make a compatibility
finding, or authorize an integrated distribution.

- Upstream: OrcaSlicer `v2.3.2`
- Release commit: `c724a3f5f51c52336624b689e846c8fbc943a912`
- Archive URL: `https://github.com/OrcaSlicer/OrcaSlicer/archive/refs/tags/v2.3.2.tar.gz`
- Retained archive: `C:\Users\coolg\Documents\Codex\forge-gate1-evidence\OrcaSlicer-v2.3.2-source.tar.gz`
- SHA-256: `2c7eea7b1e3757011f2c9520dc1712d789b9182b5c276aba271bf814172b0a52`
- Byte length: `118753412`

## Filename-level findings

The archive contains **17,637 members**. The bounded marker scan found:

- **24** license/copyright marker filenames (`LICENSE`, `COPYING`, or `NOTICE`,
  including common extensions).
- **57** CMake build manifests.
- **8** JavaScript `package.json` manifests, including Swiper web assets and
  their checked-in `node_modules` metadata.
- **2,263** members below `deps/` or `deps_src/`, indicating a substantial
  vendored/dependency tree that requires separate license and provenance
  review.

Representative markers include the root `LICENSE.txt`, Expat, GLEW, AGG,
Earcut, Eigen, ImGui, libnest2d, MCUT, md4c, minilzo, miniz, qhull, Swiper,
and Catch2 license files, plus the root and dependency CMake manifests.

## Limitations and next evidence

This inventory is based on archive member names only. It does not establish
which files are compiled, shipped, generated, downloaded, or reachable at
runtime. It also does not replace a file-level SPDX/header scan, dependency
license compatibility review, Bambu networking exclusion proof, SBOM, source
offer, or legal review. Those remain open rows in
[`GATE-1-EVIDENCE-INDEX.md`](GATE-1-EVIDENCE-INDEX.md).

The archive remains isolated from the trusted FORGE tree. Any later source
inspection must preserve the pin, digest, and a reproducible audit trail.
